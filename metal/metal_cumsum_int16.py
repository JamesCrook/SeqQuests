#!/usr/bin/env python3
"""
Metal int16 implementation using zero-copy buffers.
This is the most efficient approach - Metal writes directly to numpy memory.
"""

import numpy as np
import Metal
import ctypes

# Metal shader
shader_source = """
#include <metal_stdlib>
using namespace metal;

kernel void cumulative_sum_columns(
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device int* final_sums [[buffer(2)]],
    constant uint& num_rows [[buffer(3)]],
    constant uint& num_cols [[buffer(4)]],
    uint col_id [[thread_position_in_grid]])
{
    if (col_id >= num_cols) return;
    
    int accumulator = 0;
    
    // Ripple-carry down the column
    for (uint row = 0; row < num_rows; row++) {
        uint idx = row * num_cols + col_id;
        short value = input[idx];
        accumulator += value;
        output[idx] = (short)accumulator;
    }
    
    final_sums[col_id] = accumulator;
}
"""

def create_zero_copy_buffer(device, np_array):
    """
    Create a Metal buffer that shares memory with a numpy array.

    WARNING: The caller is responsible for keeping the 'np_array'
    object alive for the entire lifetime of the returned Metal buffer.
    """
    # 1. Ensure the array's data is in one contiguous block
    #    (This step is still important)
    np_array = np.ascontiguousarray(np_array)

    # 2. Pass the memoryview (np_array.data) directly.
    #    pyobjc will get the void* pointer from this.
    return device.newBufferWithBytesNoCopy_length_options_deallocator_(
        np_array.data,      # <--- THIS IS THE FIX
        np_array.nbytes,
        0,  # MTLResourceStorageModeShared
        None  # This means YOU must manage the np_array's lifetime
    )

def create_input_buffer(device, np_array):
    """Create input buffer (regular copy, more efficient)."""
    # np_array.data is a memoryview, pyobjc can read this
    # directly without the .tobytes() intermediate copy.
    return device.newBufferWithBytes_length_options_(
        np_array.data, 
        np_array.nbytes, 
        0
    )


def main():
    # Setup
    rows, cols = 300, 32
    np.random.seed(42)
    input_data = np.random.randint(0, 6, size=(rows, cols), dtype=np.int16)
    
    print(f"Metal int16 Zero-Copy Implementation")
    print(f"Matrix: {rows}x{cols}")
    print(f"Sample input:\n{input_data[:5, :5]}\n")
    
    # Pre-allocate output arrays - IMPORTANT: these must stay in scope!
    output_data = np.zeros((rows, cols), dtype=np.int16, order='C')
    final_sums = np.zeros(cols, dtype=np.int32, order='C')
    
    # Metal setup
    device = Metal.MTLCreateSystemDefaultDevice()
    if not device:
        raise RuntimeError("Metal not available")
    
    print(f"Device: {device.name()}")
    
    # Compile shader
    library, error = device.newLibraryWithSource_options_error_(shader_source, None, None)
    if error:
        raise RuntimeError(f"Shader compilation failed: {error}")
    
    kernel = library.newFunctionWithName_("cumulative_sum_columns")
    pipeline, error = device.newComputePipelineStateWithFunction_error_(kernel, None)
    if error:
        raise RuntimeError(f"Pipeline creation failed: {error}")
    
    # Create buffers
    # Input buffer - regular copy (input is read-only)
    input_buffer = create_input_buffer(device, input_data)
    
    # Output buffers - zero copy (Metal writes directly to numpy arrays)
    output_buffer = create_zero_copy_buffer(device, output_data)
    sums_buffer = create_zero_copy_buffer(device, final_sums)
    
    # Constants - regular copy (small and read-only)
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))
    
    print("✅ Buffers created (zero-copy for outputs)")
    
    # Execute
    queue = device.newCommandQueue()
    command_buffer = queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    encoder.setComputePipelineState_(pipeline)
    encoder.setBuffer_offset_atIndex_(input_buffer, 0, 0)
    encoder.setBuffer_offset_atIndex_(output_buffer, 0, 1)
    encoder.setBuffer_offset_atIndex_(sums_buffer, 0, 2)
    encoder.setBuffer_offset_atIndex_(rows_buffer, 0, 3)
    encoder.setBuffer_offset_atIndex_(cols_buffer, 0, 4)
    
    # Dispatch
    encoder.dispatchThreads_threadsPerThreadgroup_(
        Metal.MTLSizeMake(cols, 1, 1),
        Metal.MTLSizeMake(min(cols, pipeline.maxTotalThreadsPerThreadgroup()), 1, 1)
    )
    
    encoder.endEncoding()
    command_buffer.commit()
    command_buffer.waitUntilCompleted()
    
    print("✅ Computation complete")
    print("✅ Results already in numpy arrays (zero-copy)\n")
    
    # The results are already in output_data and final_sums!
    # No need to copy anything.
    
    # Verify results
    cumsum_numpy = np.cumsum(input_data, axis=0)
    expected_sums = cumsum_numpy[-1, :].astype(np.int32)
    
    print("Verification:")
    print(f"Metal sums: {final_sums[:8]}...")
    print(f"NumPy sums: {expected_sums[:8]}...")
    
    if np.allclose(final_sums, expected_sums):
        print("\n✅ Perfect match! Zero-copy int16 working correctly.")
        print("\nAdvantages of this approach:")
        print("• Zero memory copies for output")
        print("• Native int16 operations")
        print("• 2x memory bandwidth vs int32")
        print("• Direct numpy array access")
        print("• Maximum possible performance")
    else:
        print(f"\n❌ Mismatch: max diff = {np.max(np.abs(final_sums - expected_sums))}")
    
    # Show that we can use the results immediately
    print(f"\nColumn 0 cumulative sum (first 10 rows):")
    print(f"Result: {output_data[:10, 0]}")
    print(f"Expected: {cumsum_numpy[:10, 0]}")

if __name__ == "__main__":
    main()
