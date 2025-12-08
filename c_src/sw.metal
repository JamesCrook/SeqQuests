#include <metal_stdlib>
using namespace metal;

#ifndef THREADS
#define THREADS (4096)
#endif

#ifndef UNROLL
#define UNROLL (32)
#endif

kernel void sw_step(
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device short* carry_forward_in  [[buffer(4)]],
    device short* carry_forward_out [[buffer(5)]],
    device short* final_max_out [[buffer(6)]],
    constant uint& num_rows [[buffer(7)]],
    uint thread_id [[thread_position_in_grid]])
{
    if (thread_id >= THREADS) return;
    
    // Arrays for unrolled loop
    short accumulator[UNROLL];
    short maxv[UNROLL];
    short dValue = 0;
    short next_dValue = 0;
    short result;
    
    // Initialize arrays
    for (uint j = 0; j < UNROLL; j++) {
        accumulator[j] = 0;
        maxv[j] = 0;
    }
    
    uint base_idx = thread_id * num_rows;
    
    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        short hValue = input[idx];
        dValue = next_dValue;
        next_dValue = hValue;

        for (uint j = 0; j < UNROLL; j++) {
            short residue = aa[thread_id*UNROLL + j];
            uint nidx = residue * num_rows + row;
            short penalty = select((short)10, (short)32767, residue == 0);
            
            result = max(accumulator[j], hValue) - penalty;
            result = max(result, (short)(dValue+pam[nidx]));
            result = max(result, (short)0);
            maxv[j] = max(result, maxv[j]);
            dValue = accumulator[j];
            hValue = result; // free, just a renaming...
            accumulator[j] = result;
        }
        
        output[idx] = hValue;
    }
    
    // Column maxes at even locations,
    // Cumulative column max for this sequence at odd locations.
    // Collect the max left by a previous run of this kernel
    short prevMax = carry_forward_in[thread_id];
    for (uint j = 0; j < UNROLL; j++) {
        uint addr = thread_id*UNROLL + j;
        // update with this column max
        prevMax = max(maxv[j], prevMax );
        final_max_out[addr*2] = maxv[j];
        final_max_out[addr*2 + 1] = prevMax;
        // Reset max after a sequence boundary
        short residue = aa[addr];
        prevMax = select(prevMax, (short)0, residue == 0 );
    }
    carry_forward_out[thread_id] = prevMax;
}