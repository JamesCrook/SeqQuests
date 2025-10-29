#!/usr/bin/env python3
"""
Refactored Metal implementation for col-wise operations,
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

kernel void cumulative_sum_cols( 
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device int* final_sums [[buffer(4)]],
    constant uint& num_cols [[buffer(5)]],
    constant uint& num_rows [[buffer(6)]],
    uint col_id [[thread_position_in_grid]])
{
    if (col_id >= num_cols) return;
    
    short accumulator = 0;
    uint base_idx = col_id * num_rows;

    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        accumulator += input[idx];
        output[idx] = (short)accumulator;
    }
    
    final_sums[col_id] = accumulator;
}
"""

nws_shader_source = """
#include <metal_stdlib>
using namespace metal;

kernel void nws_step( 
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device int* final_sums [[buffer(4)]],
    constant uint& num_cols [[buffer(5)]],
    constant uint& num_rows [[buffer(6)]],
    uint col_id [[thread_position_in_grid]])
{
    if (col_id >= num_cols) return;
    
    short accumulator = 0;
    
    uint base_idx = col_id * num_rows+1;
    uint base_nidx = aa[col_id] * num_rows;
    
    for (uint row = 1; row < num_rows; row++) {
        uint idx = base_idx + row;
        uint nidx = base_nidx + row;
        short dValue = input[idx-1] + pam[nidx];
        short hValue = input[idx];
        accumulator = max( accumulator, hValue )-10;
        accumulator = max( accumulator, dValue );
        accumulator = max( accumulator, (short)0 );
        output[idx] = (short)accumulator;
    }
    
    final_sums[col_id] = accumulator;
}
"""


# --- Buffer Utilities (Unchanged) ---

def create_zero_copy_buffer(device, np_array):
    np_array = np.ascontiguousarray(np_array)
    return device.newBufferWithBytesNoCopy_length_options_deallocator_(
        np_array.data,
        np_array.nbytes,
        0, 
        None
    )

def create_input_buffer(device, np_array):
    return device.newBufferWithBytes_length_options_(
        np_array.data,
        np_array.nbytes,
        0
    )


# --- Core Subroutines (Unchanged) ---

def compile_shader(device, source, kernel_name):
    library, error = device.newLibraryWithSource_options_error_(source, None, None)
    if error:
        raise RuntimeError(f"Shader compilation failed: {error}")
    
    kernel = library.newFunctionWithName_(kernel_name)
    pipeline, error = device.newComputePipelineStateWithFunction_error_(kernel, None)
    if error:
        raise RuntimeError(f"Pipeline creation failed: {error}")
    
    return pipeline


# --- Cumulative Sum Functions ---

# CHANGED: The dispatch grid size is now a parameter
def invoke_pass(device, pipeline, buffer_input, buffer_output, buffer_pam, buffer_aa, buffer_sums, cols_buffer, rows_buffer, grid_width):
    """Invokes one pass of the cumulative_sum shader."""
    
    queue = device.newCommandQueue()
    command_buffer = queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    encoder.setComputePipelineState_(pipeline)
    encoder.setBuffer_offset_atIndex_(buffer_input, 0, 0)
    encoder.setBuffer_offset_atIndex_(buffer_output, 0, 1)
    encoder.setBuffer_offset_atIndex_(buffer_pam, 0, 2)
    encoder.setBuffer_offset_atIndex_(buffer_aa, 0, 3)
    encoder.setBuffer_offset_atIndex_(buffer_sums, 0, 4)
    encoder.setBuffer_offset_atIndex_(cols_buffer, 0, 5)
    encoder.setBuffer_offset_atIndex_(rows_buffer, 0, 6)
    
    # CHANGED: Dispatch 1D grid, one thread per col
    # The grid_width is now colS, not rowS.
    encoder.dispatchThreads_threadsPerThreadgroup_(
        Metal.MTLSizeMake(grid_width, 1, 1),
        Metal.MTLSizeMake(min(grid_width, pipeline.maxTotalThreadsPerThreadgroup()), 1, 1)
    )
    
    encoder.endEncoding()
    command_buffer.commit()
    command_buffer.waitUntilCompleted()

# CHANGED: Perform cumulative sum along axis=1 (cols)
def invoke_numpy_cumsum(input_data):
    """Performs the equivalent cumulative sum using numpy."""
    return np.cumsum(input_data, axis=1) # CHANGED: axis=0 to axis=1

# CHANGED: Verification logic updated for col-wise sums
def display_cumsum_results(input_data, metal_output, metal_sums, numpy_output):
    """Compares and displays Metal vs. Numpy cumsum results."""
    
    # CHANGED: Expected sums are the LAST rowUMN of the numpy result
    expected_sums = numpy_output[:, -1].astype(np.int32)
    
    print("Verification:")
    print(f"Metal sums: {metal_sums[:8]}...")
    print(f"NumPy sums: {expected_sums[:8]}...")
    
    if np.allclose(metal_sums, expected_sums):
        print("\n✅ Perfect match.")
    else:
        print(f"\n❌ Mismatch: max diff = {np.max(np.abs(metal_sums - expected_sums))}")
    
    # CHANGED: Print col 0 to check col-wise sum
    print(f"\ncol 0 cumulative sum (first 10 rows):")
    print(f"Result: {metal_output[0, :10]}")
    print(f"Expected: {numpy_output[0, :10]}")

def test_cumsum(device):
    """Tests the cumulative sum shader."""
    print("\n--- Testing Cumulative Sum (col-Wise) ---") # CHANGED: Title
    
    # Setup
    cols, rows = 32, 300
    np.random.seed(42)
    input_data = np.random.randint(0, 6, size=(cols, rows), dtype=np.int16)
    
    print(f"Matrix: {cols}x{rows}")
    print(f"Sample input:\n{input_data[:5, :5]}\n")
    
    # Pre-allocate output arrays
    output_data = np.zeros((cols, rows), dtype=np.int16, order='C')
    final_sums = np.zeros(cols, dtype=np.int32, order='C')

    pam_data = np.zeros((rows *32), dtype=np.int16, order='C')
    aa_data = np.zeros((cols), dtype=np.int16, order='C')

    # Compile
    pipeline = compile_shader(device, cumsum_shader_source, "cumulative_sum_cols")
    
    # Create buffers
    buffer_input = create_zero_copy_buffer(device, input_data)
    buffer_output = create_zero_copy_buffer(device, output_data)
    buffer_sums = create_zero_copy_buffer(device, final_sums) # Uses new `final_sums`
    buffer_pam = create_zero_copy_buffer(device, pam_data )
    buffer_aa = create_zero_copy_buffer(device, aa_data )

    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    
    print("Buffers created (zero-copy)")
    
    # Invoke Shader
    invoke_pass(device, pipeline, buffer_input, buffer_output, buffer_pam, buffer_aa, buffer_sums, cols_buffer, rows_buffer, cols)
    print("Computation complete")

    # Invoke Numpy
    cumsum_numpy = invoke_numpy_cumsum(input_data)
    
    # Display Results
    display_cumsum_results(input_data, output_data, final_sums, cumsum_numpy)


# --- NWS (Needleman-Wunsch-Smith) Functions ---

def display_nws_results(initial_data, final_data, num_steps):
    print("\nNWS Verification (Placeholder):")
    print(f"Initial data (top-left):\n{initial_data[:5, :5]}")
    print(f"Data after {num_steps} steps (top-left):\n{final_data[:5, :5]}")
    
    expected_data = initial_data + num_steps
    if np.allclose(final_data, expected_data):
        print("\n✅ Perfect match (for placeholder logic).")
    else:
        print("\n❌ Mismatch (for placeholder logic).")

def test_nws(device):
    print("\n--- Testing NWS Buffer Alternation ---")
    # Setup
    cols, rows = 32, 300
    num_steps = 17

    np.random.seed(42)
    initial_data = np.random.randint(0, 10, size=(cols, rows), dtype=np.int16)
    data_array_0 = initial_data.copy()
    data_array_1 = np.zeros((cols, rows), dtype=np.int16, order='C')
    
    print(f"Matrix: {cols}x{rows}, Steps: {num_steps}")
    print(f"Sample input:\n{initial_data[:5, :5]}\n")
    
    final_sums = np.zeros(cols, dtype=np.int32, order='C')
    pam_data = np.zeros((rows *32), dtype=np.int16, order='C')
    aa_data = np.zeros((cols), dtype=np.int16, order='C')

    # Compile
    pipeline = compile_shader(device, nws_shader_source, "nws_step")
    
    # Create buffers
    buffer_0 = create_zero_copy_buffer(device, data_array_0)
    buffer_1 = create_zero_copy_buffer(device, data_array_1)
    buffer_sums = create_zero_copy_buffer(device, final_sums) # Uses new `final_sums`
    buffer_pam = create_zero_copy_buffer(device, pam_data )
    buffer_aa = create_zero_copy_buffer(device, aa_data )

    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    
    print("Buffers created (zero-copy)")
    
    buffers = [buffer_0, buffer_1]
    
    print(f"Running {num_steps} steps of buffer alternation...")
    for step in range(num_steps):
        in_idx = step % 2
        out_idx = (step + 1) % 2
        
        print(f"  Step {step+1}: Reading from buffer {in_idx}, Writing to buffer {out_idx}")
    
        invoke_pass(device, pipeline, buffers[in_idx], buffers[out_idx], buffer_pam, buffer_aa, buffer_sums, cols_buffer, rows_buffer, cols)

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