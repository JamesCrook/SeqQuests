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
    short penalty = 10;
    if( aa[col_id]==0 )
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
    final_max[col_id*2] = maxv;
    final_max[col_id*2+1] = max( maxv, final_max[col_id*2+1]);
}
