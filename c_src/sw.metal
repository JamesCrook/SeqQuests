#include <metal_stdlib>
using namespace metal;

// THREADS and UNROLL are set in compile.sh.
// On Mac M4 THREADS is 4096 x 4
#ifndef THREADS
#define THREADS (4096)
#endif

#ifndef UNROLL
#define UNROLL (40)
#endif

// use uchar for 8 bit
// use ushort for 16 bit
// Must match the host program's choice.
#define PRECISION ushort

kernel void sw_step(
    device const PRECISION* input [[buffer(0)]],
    device PRECISION* output [[buffer(1)]],
    device const uchar* aa_query [[buffer(2)]],
    device const uchar* aa  [[buffer(3)]],
    device const PRECISION* carry_forward_in  [[buffer(4)]],
    device PRECISION* carry_forward_out [[buffer(5)]],
    device const uint* answer_index [[buffer(6)]],
    device PRECISION* final_max_out [[buffer(7)]],
    // pam values are signed
    constant char * pam[[buffer(8)]],
    constant uint& num_rows [[buffer(9)]],
    uint thread_id [[thread_position_in_grid]],
    uint local_id [[thread_index_in_threadgroup]],    
    uint tg_size [[threads_per_threadgroup]]
    )
{
    if (thread_id >= THREADS) return;

    // We're using an offset zero trick.
    const PRECISION zero = 32;
    // Arrays for unrolled loop
    PRECISION accumulator[UNROLL];
    PRECISION maxv[UNROLL];
    PRECISION dValue = zero;
    PRECISION next_dValue = zero;
    PRECISION result;
    PRECISION penalty = 10;

    threadgroup char shared_pam[32 * 32];

    // Cooperative load at start
    for (uint i = local_id ; i < 32 * 32; i += tg_size) {
        shared_pam[i] = pam[i];
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);    

    // Initialize arrays
    for (uint j = 0; j < UNROLL; j++) {
        accumulator[j] = zero;
        maxv[j] = zero;
    }
    
    uint idx = thread_id;
    uint aa_index = thread_id;
    ushort nidx = 0;
    
    uchar residues[UNROLL];
    for (uint j = 0; j < UNROLL; j++) {
        residues[j] = aa[aa_index];
        aa_index += THREADS;
    }

    for (uint row = 0; row < num_rows; row++) {
        PRECISION hValue = input[idx];
        dValue = next_dValue;
        next_dValue = hValue;

        nidx = 32 * (ushort)aa_query[row];

        for (uint j = 0; j < UNROLL; j++) {
            uchar residue = residues[j];
        
            result = max(accumulator[j], hValue) - penalty;
            result = max(result, (PRECISION)(dValue+shared_pam[nidx+residue]));
            result = max(result, zero);
            // whole column will be zero at terminator
            result = select(result, zero, residue == 0);
            maxv[j] = max(result, maxv[j]);
            dValue = accumulator[j];
            hValue = result; // free, just a renaming...
            accumulator[j] = result;
        }
        output[idx] = hValue;
        idx += THREADS;
    }
    
    // Column maxes at even locations,
    // Cumulative column max for this sequence at odd locations.
    // Collect the max left by a previous run of this kernel
    PRECISION prevMax = carry_forward_in[thread_id];
    for (uint j = 0; j < UNROLL; j++) {
        // update with this column max
        prevMax = max(maxv[j], prevMax );
        // Reset max after a sequence boundary
        uchar residue = residues[j];
        if( residue == 0){
            uint protein_ix = answer_index[ j*THREADS + thread_id];
            final_max_out[protein_ix]=prevMax-zero;
            prevMax = zero;
        }
    }
    carry_forward_out[thread_id] = prevMax;
}