#include <metal_stdlib>
using namespace metal;

#ifndef COLS
#define COLS (4096)
#endif

#ifndef UNROLL
#define UNROLL (32)
#endif

kernel void nws_step(
    device const short* input [[buffer(0)]],
    device short* output [[buffer(1)]],
    device short* pam [[buffer(2)]],
    device short* aa [[buffer(3)]],
    device short* final_max [[buffer(4)]],
    constant uint& num_rows [[buffer(5)]],
    uint col_id [[thread_position_in_grid]])
{
    if (col_id >= COLS) return;
    
    // Arrays for unrolled loop
    short accumulator[UNROLL];
    short maxv[UNROLL];
    short accold[UNROLL];
    
    // Initialize arrays
    for (uint j = 0; j < UNROLL; j++) {
        accumulator[j] = 0;
        maxv[j] = 0;
        accold[j] = 0;
    }
    
    uint base_idx = col_id * num_rows;
    
    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        short hValue = input[idx];
        
        for (uint j = 0; j < UNROLL; j++) {
            short residue = aa[col_id*UNROLL + j];
            uint nidx = residue * num_rows + row;
            short penalty = select((short)10, (short)30000, residue == 0);
            
            accumulator[j] = max(accumulator[j], hValue) - penalty;
            accumulator[j] = max(accumulator[j], (short)(accold[j]+pam[nidx]));
            accumulator[j] = max(accumulator[j], (short)0);
            maxv[j] = max(maxv[j], accumulator[j]);
            accold[j] = hValue;
            hValue = accumulator[j];
        }
        
        output[idx] = hValue;
    }
    
    // Column maxes at even locations,
    // Cumulative column max for this sequence at odd locations.
    // Collect the max left by a previous run of this kernel
    short prevMax = final_max[(col_id*UNROLL+(UNROLL-1))*2 +1];
    for (uint j = 0; j < UNROLL; j++) {
        uint addr = col_id*UNROLL + j;
        // update with this column max
        prevMax = max(maxv[j], prevMax );
        final_max[addr*2] = maxv[j];
        final_max[addr*2 + 1] = prevMax;
        // Reset max after a sequence boundary
        short residue = aa[addr];
        prevMax = select(prevMax, (short)0, residue == 0 );
    }
}