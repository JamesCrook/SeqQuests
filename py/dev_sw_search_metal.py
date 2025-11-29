#!/usr/bin/env python3
"""
Local similarity SW search, using metal
Uses zero-copy buffers for output.
This is a version for ease of development
In production the code compiled from /c_src/ is used instead.

We prepare a pam look up table, pam_lut for one probe sequence,
Then we search it against 1024 proteins in parallel.
This version is now obsolete as we have a fully C++/Metal version
"""

import numpy as np
try:
    import Metal
except ImportError:
    Metal = None
import ctypes

import sys
import os
import time
# Add the ../py directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))

import pam_converter as pam
import sequences

# --- Shaders ---

"""
The kernel works down the full length of the probe sequence, and there are 1024
instances running.
final_max is the per-columen max 
"""

sw_shader_source = """
#include <metal_stdlib>
using namespace metal;

kernel void sw_step(
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device short* final_max [[buffer(4)]],
    constant uint& num_threads [[buffer(5)]],
    constant uint& num_rows [[buffer(6)]],
    uint thread_id [[thread_position_in_grid]])
{
    if (thread_id >= num_threads) return;
    
    short accumulator = 0;
    short maxv = 0;
    
    uint base_idx = thread_id * num_rows;
    uint base_nidx = aa[thread_id] * num_rows;
    short penalty = 10;
    if( aa[thread_id]==0 )
        penalty = 30000;

    short dValue = 0;
    
    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        uint nidx = base_nidx + row;
        
        short hValue = input[idx];
        
        accumulator = max( accumulator, hValue )-penalty;
        accumulator = max( accumulator, dValue );
        accumulator = max( accumulator, (short)0 );
        maxv = max( maxv, accumulator );
        dValue = hValue + pam[nidx];
        
        output[idx] = (short)accumulator;
    }
    final_max[thread_id*2] = maxv;
    final_max[thread_id*2+1] = max( maxv, final_max[thread_id*2+1]);
}
"""


def sw_step(input_arr, output_arr, pam, aa, final_max, num_threads, num_rows):
    """
    Python implementation of the sw_step Metal kernel.
    """
    
    input_flat = input_arr.ravel()
    output_flat = output_arr.ravel()
    
    for thread_id in range(num_threads):
        accumulator = np.int16(0)
        maxv = np.int16(0)
        
        base_idx = thread_id * num_rows
        base_nidx = int(aa[thread_id]) * num_rows
        penalty = 10;
        if aa[thread_id]==0 :
            penalty = 30000;

        dValue = np.int16(0)
        
        for row in range(0, num_rows):
            idx = base_idx + row
            nidx = base_nidx + row
            
            hValue = np.int16(input_flat[idx])
            
            accumulator = np.int16(max(int(accumulator), int(hValue)) - penalty)
            accumulator = np.int16(max(int(accumulator), int(dValue)))
            accumulator = np.int16(max(int(accumulator), 0))
            maxv = np.int16(max(int(maxv), int(accumulator)))
            dValue = np.int16(int(hValue) + int(pam[nidx]))

            output_flat[idx] = accumulator
        
        final_max[thread_id*2] = maxv
        final_max[thread_id*2+1] = np.int16(max(int(maxv), int(final_max[thread_id*2+1])))

# --- Buffer Utilities ---

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


def invoke_pass(queue, pipeline, buffer_input, buffer_output, buffer_pam, buffer_aa, buffer_sums, threads_buffer, rows_buffer, grid_width):
    """Invokes one pass of the cumulative_sum shader."""
    
    command_buffer = queue.commandBuffer()
    encoder = command_buffer.computeCommandEncoder()
    
    encoder.setComputePipelineState_(pipeline)
    encoder.setBuffer_offset_atIndex_(buffer_input, 0, 0)
    encoder.setBuffer_offset_atIndex_(buffer_output, 0, 1)
    encoder.setBuffer_offset_atIndex_(buffer_pam, 0, 2)
    encoder.setBuffer_offset_atIndex_(buffer_aa, 0, 3)
    encoder.setBuffer_offset_atIndex_(buffer_sums, 0, 4)
    encoder.setBuffer_offset_atIndex_(threads_buffer, 0, 5)
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

# --- SW (Smith-Waterman) Functions ---
def make_metal_buffers(device, threads, rows):
    """Creates and returns a dictionary of Metal buffers and related data."""
    print("\n--- Initializing Metal Buffers ---")

    initial_data = np.zeros((threads, rows), dtype=np.int16, order='C')
    data_array_0 = np.zeros((threads, rows), dtype=np.int16, order='C')
    data_array_1 = np.zeros((threads, rows), dtype=np.int16, order='C')
    
    final_max = np.zeros(threads*2, dtype=np.int16, order='C')
    pam_data = np.zeros((rows * 32), dtype=np.int16, order='C')
    aa_data = np.zeros(threads, dtype=np.int16, order='C')

    pipeline = compile_shader(device, sw_shader_source, "sw_step")
    
    buffers = {
        'device': device,
        'pipeline': pipeline,
        'data_buffers': [
            create_zero_copy_buffer(device, data_array_0),
            create_zero_copy_buffer(device, data_array_1)
        ],
        'pam_buffer': create_zero_copy_buffer(device, pam_data),
        'aa_buffer': create_zero_copy_buffer(device, aa_data),
        'max_buffer': create_zero_copy_buffer(device, final_max),
        'threads_buffer': create_input_buffer(device, np.array([threads], dtype=np.uint32)),
        'rows_buffer': create_input_buffer(device, np.array([rows], dtype=np.uint32)),
        'numpy_buffers': [data_array_0, data_array_1],
        'pam_data': pam_data,
        'aa_data': aa_data,
        'final_max': final_max,
        'initial_data': initial_data
    }
    
    print(f"Matrix: {threads}x{rows}")
    print("Buffers created (zero-copy)")
    return buffers
    
# Fills aa_data for typically 1024 proteins.
def yield_aa_old(threads, aa_data, final_max):
    """Generator that yields aa_data for each sequence."""
    # aa_data is memory mapped, so we fill it in place.
    fasta_iter = sequences.read_fasta_sequences()
    
    # Initialize lists with proper length
    seqs = [""] * threads
    names = [""] *threads
    pos = [0] * threads
    seqno = [-1] *threads
    seq=-1
    
    while True:
        for i in range(threads):
            # Check if we need to load the next sequence
            length = len(seqs[i])
            if pos[i] >= length:
                try:
                    score = final_max[2*i+1]
                    cscore = final_max[2*i]
                    if( score > 100 ):
                        print(f"Slot:{i:>4} Seq:{seqno[i]:>6} Length:{length-1:>4} Score:{score:>5} Name:{names[i][:100]}")
                    final_max[2*i+1]=0
                    seq += 1
                    rec = next(fasta_iter)
                    # @ is the stop char, end of sequence.
                    seqs[i] = "@" + rec.seq
                    #seqs[i] = "@MAFSAEDVLKEYDRRRRMEALLLSLYYPNDRKLLDYKEWSPPRVQ"
                    pos[i] = 0
                    seqno[i] = seq
                    names[i] = rec.description
                except StopIteration:
                    return  # End generator when any position runs out.
            
            # Extract amino acid and encode it
            aa_data[i] = ord(seqs[i][pos[i]]) % 32
            pos[i] += 1
        
        yield aa_data    

def yield_aa(threads, aa_data, final_max):
    """Generator that yields aa_data for each sequence."""
    fasta_iter = sequences.read_fasta_sequences()
    
    # ONLY CHANGE: seqs stores bytes, not strings
    seqs = [b''] * threads
    names = [""] * threads
    pos = [0] * threads
    seqno = [-1] * threads
    seq = -1
    
    while True:
        for i in range(threads):
            length = len(seqs[i])
            if pos[i] >= length:
                try:
                    score = final_max[2*i+1]
                    # cscore = final_max[2*i]
                    if score > 100:
                        print(f"Slot:{i:>4} Seq:{seqno[i]:>6} Length:{length-1:>4} Score:{score:>5} Name:{names[i][:100]}")
                    final_max[2*i+1] = 0
                    seq += 1
                    rec = next(fasta_iter)
                    
                    # If rec.seq is already bytes (from pickle), use directly
                    # Otherwise convert once:
                    if isinstance(rec.seq, bytes):
                        seqs[i] = b'@' + rec.seq
                    else:
                        seqs[i] = ('@' + rec.seq).encode('latin-1')
                    
                    pos[i] = 0
                    seqno[i] = seq
                    names[i] = rec.description
                except StopIteration:
                    return
            
            aa_data[i] = seqs[i][pos[i]] & 31
            pos[i] += 1
        
        yield True


def run_metal_steps(all_buffers, threads, rows):
    """Runs the SW comparison until we run out of database."""
    device = all_buffers['device']
    pipeline = all_buffers['pipeline']
    buffers = all_buffers['data_buffers']
    pam_buffer = all_buffers['pam_buffer']
    aa_buffer = all_buffers['aa_buffer']
    max_buffer = all_buffers['max_buffer']
    threads_buffer = all_buffers['threads_buffer']
    rows_buffer = all_buffers['rows_buffer']
    buffc = all_buffers['numpy_buffers']
    aa_data = all_buffers['aa_data']
    pam_data = all_buffers['pam_data']
    final_max = all_buffers['final_max']
    initial_data = all_buffers['initial_data']

    queue = device.newCommandQueue()
    gen = yield_aa(threads, aa_data, final_max)
    use_metal = True
    dummy_step = False

    print(f"Running SW steps...")
    start = time.time()
    step =-1
    work = None

    for work in gen:
        step +=1

        in_idx, out_idx = step % 2, (step + 1) % 2
        #print(f"  Step {step+1}: Reading from buffer {in_idx}, Writing to buffer {out_idx}")

        if dummy_step :
            pass
        elif use_metal:
            invoke_pass(
                queue, pipeline, buffers[in_idx], buffers[out_idx],
                pam_buffer, aa_buffer, max_buffer,
                threads_buffer, rows_buffer, threads
            )
        else :
            sw_step(buffc[in_idx], buffc[out_idx], pam_data, aa_data,
                final_max, threads, rows)

    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.4f} seconds")

def search_db(device):
    """Configures and runs a database search."""
    pam_32x32, _ = pam.convert_pam_to_32x32()
    fasta_iter = sequences.read_fasta_sequences()
    first_record = next(fasta_iter)
    pam_lut, sequence = pam.make_fasta_lut(first_record, pam_32x32)

    threads, rows = 1024, len(sequence)
    all_buffers = make_metal_buffers(device, threads, rows)

    pam_view = np.array(pam_lut, dtype=np.int16).flatten()
    all_buffers['pam_data'][:] = pam_view

    run_metal_steps(all_buffers, threads, rows)


# --- Main ---

def main():
    device = Metal.MTLCreateSystemDefaultDevice()
    if not device:
        raise RuntimeError("Metal not available")
    print(f"Device: {device.name()}")
    
    search_db(device)

if __name__ == "__main__":
    main()