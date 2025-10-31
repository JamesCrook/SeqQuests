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

nws_shader_source = """
#include <metal_stdlib>
using namespace metal;

kernel void nws_step( 
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device short* final_max [[buffer(4)]],
    constant uint& num_cols [[buffer(5)]],
    constant uint& num_rows [[buffer(6)]],
    uint col_id [[thread_position_in_grid]])
{
    if (col_id >= num_cols) return;
    
    short accumulator = 0;
    short maxv = 0;
    
    uint base_idx = col_id * num_rows;
    uint base_nidx = aa[col_id] * num_rows;
    short dValue = 0;
    
    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        uint nidx = base_nidx + row;
        
        short hValue = input[idx];
        
        accumulator = max( accumulator, hValue )-10;
        accumulator = max( accumulator, dValue );
        accumulator = max( accumulator, (short)0 );
        maxv = max( maxv, accumulator );
        dValue = hValue + pam[nidx];
        
        output[idx] = (short)accumulator;
    }
    final_max[col_id] = maxv;
}
"""


def nws_step(input_arr, output_arr, pam, aa, final_max, num_cols, num_rows):
    """
    Python implementation of the nws_step Metal kernel.
    
    Parameters:
    -----------
    input_arr : np.ndarray
        Input array of shape that can be indexed by (col_id * num_rows + row)
    output_arr : np.ndarray
        Output array with same indexing as input_arr
    pam : np.ndarray
        Parameter array
    aa : np.ndarray
        Array of indices for each column
    final_max : np.ndarray
        Array to store final accumulator values for each column
    num_cols : int
        Number of columns to process
    num_rows : int
        Number of rows per column
    """
    
    input_flat = input_arr.ravel()
    output_flat = output_arr.ravel()
    
    for col_id in range(num_cols):
        accumulator = np.int16(0)
        maxv = np.int16(0)
        
        base_idx = col_id * num_rows
        base_nidx = int(aa[col_id]) * num_rows
        dValue = np.int16(0)
        
        for row in range(0, num_rows):
            idx = base_idx + row
            nidx = base_nidx + row
            
            hValue = np.int16(input_flat[idx])
            
            accumulator = np.int16(max(int(accumulator), int(hValue)) - 10)
            accumulator = np.int16(max(int(accumulator), int(dValue)))
            accumulator = np.int16(max(int(accumulator), 0))
            maxv = np.int16(max(int(maxv), int(accumulator)))
            dValue = np.int16(int(hValue) + int(pam[nidx]))

            output_flat[idx] = accumulator
        
        final_max[col_id] = maxv

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


def compile_shader(device, source, kernel_name):
    library, error = device.newLibraryWithSource_options_error_(source, None, None)
    if error:
        raise RuntimeError(f"Shader compilation failed: {error}")
    
    kernel = library.newFunctionWithName_(kernel_name)
    pipeline, error = device.newComputePipelineStateWithFunction_error_(kernel, None)
    if error:
        raise RuntimeError(f"Pipeline creation failed: {error}")
    
    return pipeline


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

# --- NWS (Needleman-Wunsch-Smith) Functions ---

def display_nws_results(initial_data, final_data, final_max, num_steps):
    print("\nNWS Verification (Placeholder):")
    print(f"Initial data (top-left):\n{initial_data[:5, :5]}")
    print(f"Data after {num_steps} steps (top-left):\n{final_data[:5, :5]}")
    print(f"Final Max:\n{final_max[:5]}")
    return

    expected_data = initial_data + num_steps
    if np.allclose(final_data, expected_data):
        print("\n✅ Perfect match (for placeholder logic).")
    else:
        print("\n❌ Mismatch (for placeholder logic).")


def test_nws(device):
    print("\n--- Testing NWS Buffer Alternation ---")
    # Setup
    cols, rows = 5, 300
    num_steps = 2

    np.random.seed(42)
    initial_data = np.random.randint(0, 10, size=(cols, rows), dtype=np.int16)
    data_array_0 = initial_data.copy()
    data_array_1 = np.zeros((cols, rows), dtype=np.int16, order='C')
    
    print(f"Matrix: {cols}x{rows}, Steps: {num_steps}")
    print(f"Sample input:\n{initial_data[:5, :5]}\n")
    
    final_max = np.zeros(cols, dtype=np.int16, order='C')
    pam_data = np.zeros((rows *32), dtype=np.int16, order='C')
    aa_data = np.zeros((cols), dtype=np.int16, order='C')

    # Compile
    pipeline = compile_shader(device, nws_shader_source, "nws_step")
    
    # Create buffers
    buffer_0 = create_zero_copy_buffer(device, data_array_0)
    buffer_1 = create_zero_copy_buffer(device, data_array_1)
    buffer_max = create_zero_copy_buffer(device, final_max) # Uses new `final_sums`
    buffer_pam = create_zero_copy_buffer(device, pam_data )
    buffer_aa = create_zero_copy_buffer(device, aa_data )

    # These are two numbers.
    cols_buffer = create_input_buffer(device, np.array([cols], dtype=np.uint32))
    rows_buffer = create_input_buffer(device, np.array([rows], dtype=np.uint32))
    
    print("Buffers created (zero-copy)")
    
    buffers = [buffer_0, buffer_1]
    buffc = [data_array_0, data_array_1]
    
    print(f"Running {num_steps} steps of buffer alternation...")
    for step in range(num_steps):
        in_idx = step % 2
        out_idx = (step + 1) % 2
        
        print(f"  Step {step+1}: Reading from buffer {in_idx}, Writing to buffer {out_idx}")

        nws_step(buffc[in_idx], buffc[out_idx], pam_data, aa_data, final_max, cols, rows)
        #invoke_pass(device, pipeline, buffers[in_idx], buffers[out_idx], buffer_pam, buffer_aa, buffer_max, cols_buffer, rows_buffer, cols)

    final_array_np = [data_array_0, data_array_1][num_steps % 2]
    
    display_nws_results(initial_data, final_array_np, final_max, num_steps)
        

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