#include <metal_stdlib>
using namespace metal;

#ifndef COLS
#define COLS (4096)
#endif

#ifndef UNROLL
#define UNROLL (1)
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

    short accumulator = 0;
    short maxv = 0;

    uint base_idx = col_id * num_rows;
    uint base_nidx = aa[col_id] * num_rows;
    short residue = aa[col_id];

    short dValue = 0;

    for (uint row = 0; row < num_rows; row++) {
        uint idx = base_idx + row;
        uint nidx = base_nidx + row;

        short hValue = input[idx];
        short penalty = select(10,30000, residue == 0 );
        accumulator = max( accumulator, hValue )-penalty;
        accumulator = max( accumulator, dValue );
        accumulator = max( accumulator, (short)0 );
        maxv = max( maxv, accumulator );
        dValue = hValue + pam[nidx];

        output[idx] = (short)accumulator;
    }
    final_max[col_id*2] = maxv;
    final_max[col_id*2+1] = max( maxv, final_max[col_id*2+1]);
}
