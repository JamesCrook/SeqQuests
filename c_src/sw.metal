#include <metal_stdlib>
using namespace metal;

#ifndef THREADS
#define THREADS (4096)
#endif

#ifndef UNROLL
#define UNROLL (40)
#endif

kernel void sw_step(
    device const uchar* input [[buffer(0)]],
    device uchar* output [[buffer(1)]],
    device const uchar* pam [[buffer(2)]],
    device const uchar* aa  [[buffer(3)]],
    device const uchar* carry_forward_in  [[buffer(4)]],
    device uchar* carry_forward_out [[buffer(5)]],
    device const int* answer_index [[buffer(6)]],
    device uchar* final_max_out [[buffer(7)]],
    constant uint& num_rows [[buffer(8)]],
    uint thread_id [[thread_position_in_grid]])
{
    if (thread_id >= THREADS) return;

    // We're using an offset zero trick.
    const uchar zero = 32;
    // Arrays for unrolled loop
    uchar accumulator[UNROLL];
    uchar maxv[UNROLL];
    uchar dValue = zero;
    uchar next_dValue = zero;
    uchar result;
    uchar penalty = 10;
    
    // Initialize arrays
    for (uint j = 0; j < UNROLL; j++) {
        accumulator[j] = zero;
        maxv[j] = zero;
    }
    
    uint base_idx = thread_id * num_rows;
    uint aa_index = thread_id * UNROLL;
    uint nidx = 0;
    
    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        uchar hValue = input[idx];
        dValue = next_dValue;
        next_dValue = hValue;

        for (uint j = 0; j < UNROLL; j++) {
            uchar residue = (uchar)aa[ aa_index + j];
        
            result = max(accumulator[j], hValue) - penalty;
            result = max(result, (uchar)(dValue+(uchar)pam[nidx+residue]));
            result = max(result, (uchar)zero);
            // whole column will be zero at terminator
            result = select(result, (uchar)zero, residue == 0);
            maxv[j] = max(result, maxv[j]);
            dValue = accumulator[j];
            hValue = result; // free, just a renaming...
            accumulator[j] = result;
        }
        nidx += 32;
        output[idx] = hValue;
    }
    
    // Column maxes at even locations,
    // Cumulative column max for this sequence at odd locations.
    // Collect the max left by a previous run of this kernel
    uchar prevMax = carry_forward_in[thread_id];
    for (uint j = 0; j < UNROLL; j++) {
        // update with this column max
        prevMax = max(maxv[j], prevMax );
        // Reset max after a sequence boundary
        char residue = aa[aa_index + j];
        if( residue == 0){
            int protein_ix = answer_index[ aa_index + j];
            final_max_out[protein_ix]=prevMax-zero;
            prevMax = zero;
        }
    }
    carry_forward_out[thread_id] = prevMax;
}