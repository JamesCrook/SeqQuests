# Metal Compute Shader Examples with int16

* **metal_cumsum_int16.py** is a cumulative sum kernel. 
* **metal_nws.py** is a NWS comparison kernel. 

Both demonstrate using Metal compute shaders from Python on int16 data with explicit sequential processing (ripple-carry style). These are early versions, obsoleted by the C++/Metal versions.

## Features (Cumsum)

- Uses native Metal `short` (int16) type for optimal performance
- Processes 32 columns in parallel, each with 300 sequential additions
- Shows explicit carry propagation that can be modified for other algorithms
- Compares results with NumPy for verification

Note: 4096 threads and more are possible.

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

## Performance Notes

- Native int16 operations are ~2x faster than int32 for memory-bound operations
- No conditional branches in the inner loop

