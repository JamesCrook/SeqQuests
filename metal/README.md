# Metal Compute Shader Example with int16

This example demonstrates using Metal compute shaders from Python to perform cumulative sum on int16 data with explicit sequential processing (ripple-carry style).

## Features

- Uses native Metal `short` (int16) type for optimal performance
- Processes 32 columns in parallel, each with 300 sequential additions
- Shows explicit carry propagation that can be modified for other algorithms
- Compares results with NumPy for verification

## Installation

On macOS (Metal only works on Mac):

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install numpy pyobjc-framework-Metal pyobjc-framework-Cocoa
```

## Usage

```bash
python metal_cumsum_int16.py
```

## Key Code Structure

The Metal shader:
1. Each thread handles one column (32 threads total)
2. Sequential loop processes 300 rows per column
3. Accumulator carries the sum down the column
4. Direct int16 arithmetic with no packing/unpacking

## Performance Notes

- Native int16 operations are ~2x faster than int32 for memory-bound operations
- No conditional branches in the inner loop
- Optimal memory access pattern for column processing
- Can be extended to more complex sequence comparison algorithms

## Customization

To adapt for your protein sequence comparison:
1. Replace the simple addition with your scoring function
2. Add additional buffers for sequence data
3. Modify the accumulator logic for your specific algorithm
