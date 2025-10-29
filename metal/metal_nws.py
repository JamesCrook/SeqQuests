#!/usr/bin/env python3
"""
Refactored Metal implementation for column-wise operations,
demonstrating cumulative sum and a framework for buffer alternation (e.g., NWS).
Uses zero-copy buffers for output.
"""

import numpy as np
import Metal
import ctypes

# --- Shaders ---

cumsum_shader_source = """
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

nws_shader_source = """
#include <metal_stdlib>
using namespace metal;

/**
 * Placeholder kernel for a single NWS step.
 * This is just a dummy operation (add 1) to test the buffer alternation.
 * A real NWS kernel would be more complex, likely reading from
 * multiple buffers (e.g., diagonal, left, up) and a substitution matrix.
 */
kernel void nws_step(
    device const short* input_buffer [[buffer(0)]],
    device short* output_buffer [[buffer(1)]],
    constant uint& num_rows [[buffer(2)]],
    constant uint& num_cols [[buffer(3)]],
    uint2 tid [[thread_position_in_grid]]) // Use 2D grid
{
    if (tid.x >= num_cols || tid.y >= num_rows) return;
    
    uint idx = tid.y * num_cols + tid.x;
    
    // Placeholder operation: just add 1
    output_buffer[idx] = input_buffer[idx] + 1;
}
"""


# --- Buffer Utilities (from original) ---

def create_zero_copy_buffer(device, np_array):
    """
    Create a Metal buffer that shares memory with a numpy array.

    WARNING: The caller is responsible for keeping the 'np_array'
    object alive for the entire lifetime of the returned Metal buffer.
    """
    # 1. Ensure the array's data is in one contiguous block
    np_array = np.ascontiguousarray(np_array)

    # 2. Pass the memoryview (np_array.data) directly.
    return device.newBufferWithBytesNoCopy_length_options_deallocator_(
        np_array.data,
        np_array.nbytes,
        0,  # MTLResourceStorageModeShared
        None  # This means YOU must manage the np_array's lifetime
    )

def create_input_buffer(device, np_array):
    """Create input buffer (regular copy, more efficient for small data)."""
    return device.newBufferWithBytes_length_options_(
        np_array.data,
        np_array.nbytes,
        0
    )


# --- Core Subroutines ---

def compile_shader(device, source, kernel_name):
    """Compiles a Metal shader source and returns the compute pipeline."""
    library, error = device.newLibraryWithSource_options_error_(source, None, None)
    if error:
        raise RuntimeError(f"Shader compilation failed: {error}")
    
    kernel = library.newFunctionWithName_(kernel_name)
    pipeline, error = device.newComputePipelineStateWithFunction_error_(kernel, None)
    if error:
        raise RuntimeError(f"Pipeline creation failed: {error}")
    
    return pipeline


# --- Cumulative Sum Functions ---

def invoke_cumsum_pass(device, pipeline, buffer_input, buffer_output, buffer_sums, rows_buffer, cols_buffer, cols):
    """Invokes one pass of the cumulative_sum_columns shader."""
    
    queue = device.newCommandQueue()
    command_buffer = queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    encoder.setComputePipelineState_(pipeline)
    encoder.setBuffer_offset_atIndex_(buffer_input, 0, 0)
    encoder.setBuffer_offset_atIndex_(buffer_output, 0, 1)
    encoder.setBuffer_offset_atIndex_(buffer_sums, 0, 2)
    encoder.setBuffer_offset_atIndex_(rows_buffer, 0, 3)
    encoder.setBuffer_offset_atIndex_(cols_buffer, 0, 4)
    
    # Dispatch 1D grid, one thread per column
    encoder.dispatchThreads_threadsPerThreadgroup_(
        Metal.MTLSizeMake(cols, 1, 1),
        Metal.MTLSizeMake(min(cols, pipeline.maxTotalThreadsPerThreadgroup()), 1, 1)
    )
    
    encoder.endEncoding()
    command_buffer.commit()
    command_buffer.waitUntilCompleted()

def invoke_numpy_cumsum(input_data):
    """Performs the equivalent cumulative sum using numpy."""
    return np.cumsum(input_data, axis=0)

def display_cumsum_results(input_data, metal_output, metal_sums, numpy_output):
    """Compares and displays Metal vs. Numpy cumsum results."""
    
    expected_sums = numpy_output[-1, :].astype(np.int32)
    
    print("Verification:")
    print(f"Metal sums: {metal_sums[:8]}...")
    print(f"NumPy sums: {expected_sums[:8]}...")
    
    if np.allclose(metal_sums, expected_sums):
        print("\n✅ Perfect match.")
    else:
        print(f"\n❌ Mismatch: max diff = {np.max(np.abs(metal_sums - expected_sums))}")
    
    print(f"\nColumn 0 cumulative sum (first 10 rows):")
    print(f"Result: {metal_output[:10, 0]}")
    print(f"Expected: {numpy_output[:10, 0]}")

def test_cumsum(device):
    """Tests the cumulative sum shader."""
    print("\n--- Testing Cumulative Sum ---")
    
    # Setup
    rows, cols = 300, 32
    np.random.seed(42)
    input_data = np.random.randint(0, 6, size=(rows, cols), dtype=np.int16)
    
    print(f"Matrix: {rows}x{cols}")
    print(f"Sample input:\n{input_data[:5, :5]}\n")
    
    # Pre-allocate output arrays - IMPORTANT: these must stay in scope!
    output_data = np.zeros((rows, cols), dtype=np.int16, order='C')
    final_sums = np.zeros(cols, dtype=np.int32, order='C')
    
    # Compile
    pipeline = compile_shader(device, cumsum_shader_source, "cumulative_sum_columns")
    
    # Create buffers
    buffer_input = create_zero_copy_buffer(device, input_data) # Use zero-copy for input too
    buffer_output = create_zero_copy_buffer(device, output_data)
    buffer_sums = create_zero_copy_buffer(device, final_sums)
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))
    
    print("Buffers created (zero-copy)")
    
    # Invoke Shader
    invoke_cumsum_pass(device, pipeline, buffer_input, buffer_output, buffer_sums, rows_buffer, cols_buffer, cols)
    print("Computation complete")

    # Invoke Numpy
    cumsum_numpy = invoke_numpy_cumsum(input_data)
    
    # Display Results
    display_cumsum_results(input_data, output_data, final_sums, cumsum_numpy)


# --- NWS (Needleman-Wunsch-Smith) Functions ---

def invoke_nws_pass(device, pipeline, buffer_in, buffer_out, rows_buffer, cols_buffer, rows, cols):
    """Invokes one pass of the NWS placeholder shader."""
    queue = device.newCommandQueue()
    command_buffer = queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    encoder.setComputePipelineState_(pipeline)
    encoder.setBuffer_offset_atIndex_(buffer_in, 0, 0)
    encoder.setBuffer_offset_atIndex_(buffer_out, 0, 1)
    encoder.setBuffer_offset_atIndex_(rows_buffer, 0, 2)
    encoder.setBuffer_offset_atIndex_(cols_buffer, 0, 3)

    # NWS kernel uses a 2D grid
    # Calculate a reasonable threadgroup size
    max_threads = pipeline.maxTotalThreadsPerThreadgroup()
    thread_width = min(cols, 32)
    thread_height = min(rows, max_threads // thread_width)
    threads_per_group = Metal.MTLSizeMake(thread_width, thread_height, 1)
    
    grid_size = Metal.MTLSizeMake(cols, rows, 1)
    
    encoder.dispatchThreads_threadsPerThreadgroup_(grid_size, threads_per_group)
    
    encoder.endEncoding()
    command_buffer.commit()
    command_buffer.waitUntilCompleted()

def display_nws_results(initial_data, final_data, num_steps):
    """Displays the (placeholder) NWS results."""
    print("\nNWS Verification (Placeholder):")
    print(f"Initial data (top-left):\n{initial_data[:5, :5]}")
    print(f"Data after {num_steps} steps (top-left):\n{final_data[:5, :5]}")
    
    # Verification for our placeholder "add 1" shader
    expected_data = initial_data + num_steps
    if np.allclose(final_data, expected_data):
        print("\n✅ Perfect match (for placeholder logic).")
    else:
        print("\n❌ Mismatch (for placeholder logic).")

def test_nws(device):
    """Tests the buffer alternation framework for NWS."""
    print("\n--- Testing NWS Buffer Alternation ---")
    rows, cols = 300, 32
    num_steps = 17

    # Setup
    # Two numpy arrays for ping-ponging
    np.random.seed(42)    
    initial_data = np.random.randint(0, 10, size=(rows, cols), dtype=np.int16)
    data_array_0 = initial_data.copy() # Input
    data_array_1 = np.zeros((rows, cols), dtype=np.int16, order='C') # Output/Scratch
    
    print(f"Matrix: {rows}x{cols}, Steps: {num_steps}")

    pipeline = compile_shader(device, nws_shader_source, "nws_step")

    # Buffers
    buffer_0 = create_zero_copy_buffer(device, data_array_0)
    buffer_1 = create_zero_copy_buffer(device, data_array_1)
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))

    buffers = [buffer_0, buffer_1]
    
    print(f"Running {num_steps} steps of buffer alternation...")
    for step in range(num_steps):
        in_idx = step % 2
        out_idx = (step + 1) % 2
        
        print(f"  Step {step+1}: Reading from buffer {in_idx}, Writing to buffer {out_idx}")
        
        invoke_nws_pass(device, pipeline, buffers[in_idx], buffers[out_idx], 
                        rows_buffer, cols_buffer, rows, cols)

    # Result is in the last written buffer
    # Step 0: 0 -> 1. (num_steps=1, 1%2=1)
    # Step 1: 1 -> 0. (num_steps=2, 2%2=0)
    # Step 2: 0 -> 1. (num_steps=3, 3%2=1)
    final_array_np = [data_array_0, data_array_1][num_steps % 2]
    
    display_nws_results(initial_data, final_array_np, num_steps)
        

# --- Main ---

def main():
    device = Metal.MTLCreateSystemDefaultDevice()
    if not device:
        raise RuntimeError("Metal not available")
    print(f"Device: {device.name()}")
    
    #test_cumsum(device)
    test_nws(device)

if __name__ == "__main__":
    main()
