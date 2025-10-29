#!/usr/bin/env python3
"""
Metal compute shader example using int16 for cumulative sum down columns.
Shows explicit sequential processing (ripple-carry style) within each column.
"""

import numpy as np
import Metal
import objc
from Foundation import NSData

# Metal shader source code
shader_source = """
#include <metal_stdlib>
using namespace metal;

kernel void cumulative_sum_columns(
    device const short* input [[buffer(0)]],   // 32x300 matrix in row-major order
    device short* output [[buffer(1)]],         // 32x300 matrix in row-major order
    device int* final_sums [[buffer(2)]],       // 32 final sums (using int to avoid overflow)
    constant uint& num_rows [[buffer(3)]],      // 300
    constant uint& num_cols [[buffer(4)]],      // 32
    uint col_id [[thread_position_in_grid]])    // Column index (0-31)
{
    // Each thread handles one column
    if (col_id >= num_cols) return;
    
    // Initialize accumulator for this column
    int accumulator = 0;
    
    // Sequential ripple-carry down the column
    for (uint row = 0; row < num_rows; row++) {
        // Row-major indexing: row * num_cols + col
        uint idx = row * num_cols + col_id;
        
        // Read the input value
        short value = input[idx];
        
        // Add to accumulator (this is the "carry" propagation)
        accumulator += value;
        
        // Write the cumulative sum to output
        // Note: Metal handles overflow/underflow for short naturally
        output[idx] = (short)accumulator;
    }
    
    // Store the final sum for this column
    final_sums[col_id] = accumulator;
}
""";

def create_metal_device():
    """Create and return the default Metal device."""
    return Metal.MTLCreateSystemDefaultDevice()

def compile_shader(device, source):
    """Compile Metal shader source code."""
    error_ptr = objc.nil
    library = device.newLibraryWithSource_options_error_(source, None, error_ptr)
    if error_ptr:
        raise RuntimeError(f"Shader compilation failed: {error_ptr}")
    return library

def create_buffer_from_numpy(device, np_array):
    """Create a Metal buffer from a numpy array."""
    data = NSData.dataWithBytes_length_(np_array.ctypes.data, np_array.nbytes)
    buffer = device.newBufferWithData_options_(data, Metal.MTLResourceStorageModeShared)
    return buffer

def buffer_to_numpy(buffer, shape, dtype):
    """Convert a Metal buffer back to numpy array."""
    ptr = buffer.contents()
    return np.frombuffer(ptr.as_buffer(buffer.length()), dtype=dtype).reshape(shape)

def main():
    # Initialize data
    rows = 300
    cols = 32
    
    # Create input array with small random integers (0-5)
    np.random.seed(42)  # For reproducibility
    input_data = np.random.randint(0, 6, size=(rows, cols), dtype=np.int16)
    
    print(f"Input shape: {input_data.shape}")
    print(f"First 5 rows of first 5 columns:")
    print(input_data[:5, :5])
    
    # Setup Metal
    device = create_metal_device()
    if not device:
        raise RuntimeError("Metal is not supported on this device")
    
    print(f"\nUsing Metal device: {device.name()}")
    
    # Compile shader
    library = compile_shader(device, shader_source)
    kernel_function = library.newFunctionWithName_("cumulative_sum_columns")
    
    # Create compute pipeline
    error_ptr = objc.nil
    pipeline = device.newComputePipelineStateWithFunction_error_(kernel_function, error_ptr)
    if error_ptr:
        raise RuntimeError(f"Pipeline creation failed: {error_ptr}")
    
    # Create command queue
    command_queue = device.newCommandQueue()
    
    # Create buffers
    input_buffer = create_buffer_from_numpy(device, input_data)
    output_buffer = device.newBufferWithLength_options_(
        input_data.nbytes, Metal.MTLResourceStorageModeShared)
    final_sums_buffer = device.newBufferWithLength_options_(
        cols * 4, Metal.MTLResourceStorageModeShared)  # 32 ints
    
    # Create constants buffers
    rows_const = np.array([rows], dtype=np.uint32)
    cols_const = np.array([cols], dtype=np.uint32)
    rows_buffer = create_buffer_from_numpy(device, rows_const)
    cols_buffer = create_buffer_from_numpy(device, cols_const)
    
    # Create command buffer and encoder
    command_buffer = command_queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    # Set the compute pipeline
    encoder.setComputePipelineState_(pipeline)
    
    # Set buffers
    encoder.setBuffer_offset_atIndex_(input_buffer, 0, 0)
    encoder.setBuffer_offset_atIndex_(output_buffer, 0, 1)
    encoder.setBuffer_offset_atIndex_(final_sums_buffer, 0, 2)
    encoder.setBuffer_offset_atIndex_(rows_buffer, 0, 3)
    encoder.setBuffer_offset_atIndex_(cols_buffer, 0, 4)
    
    # Configure thread groups
    threads_per_threadgroup = Metal.MTLSizeMake(cols, 1, 1)  # 32 threads
    threadgroups = Metal.MTLSizeMake(1, 1, 1)  # 1 threadgroup
    
    # Dispatch threads
    encoder.dispatchThreadgroups_threadsPerThreadgroup_(threadgroups, threads_per_threadgroup)
    
    # Finish encoding and execute
    encoder.endEncoding()
    command_buffer.commit()
    command_buffer.waitUntilCompleted()
    
    # Get results
    output_data = buffer_to_numpy(output_buffer, (rows, cols), np.int16)
    final_sums_metal = buffer_to_numpy(final_sums_buffer, (cols,), np.int32)
    
    # Verify with numpy
    print("\n" + "="*50)
    print("VERIFICATION")
    print("="*50)
    
    # Compute cumulative sum using numpy
    cumsum_numpy = np.cumsum(input_data, axis=0)
    final_sums_numpy = cumsum_numpy[-1, :]  # Last row contains final sums
    
    # Compare results
    print(f"\nFinal sums from Metal:")
    print(final_sums_metal)
    print(f"\nFinal sums from NumPy:")
    print(final_sums_numpy)
    
    # Check if results match
    if np.allclose(final_sums_metal, final_sums_numpy):
        print("\n✅ Results match! Metal computation is correct.")
    else:
        print("\n❌ Results don't match!")
        diff = np.abs(final_sums_metal - final_sums_numpy)
        print(f"Maximum difference: {np.max(diff)}")
    
    # Show a sample of the cumulative sums
    print(f"\nFirst 10 rows of column 0 (cumulative sum):")
    print("Metal:", output_data[:10, 0])
    print("NumPy:", cumsum_numpy[:10, 0])
    
    # Performance note
    print("\n" + "="*50)
    print("PERFORMANCE NOTE")
    print("="*50)
    print("This runs 32 cumulative sums in parallel, each doing 300 sequential")
    print("additions with explicit carry propagation (ripple-carry style).")
    print("Each thread handles one complete column independently.")

if __name__ == "__main__":
    main()
