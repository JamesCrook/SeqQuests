# Metal SW Documentation

## Overview
`metal_sw` (compiled from `c_src/metal_sw.mm` and `c_src/sw.metal`) is the core high-performance compute engine. It uses Apple's Metal API to perform Smith-Waterman local alignment on the GPU.

## Usage

```bash
./bin/metal_sw [options]
```

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--pam_data` | Path to binary PAM matrix file (default: `pam250.bin`). |
| `--fasta_data` | Path to binary FASTA database file (default: `fasta.bin`). |
| `--start_at` | Sequence index to start processing from. |
| `--num_seqs` | Number of sequences to process. |
| `--reporting_threshold` | Minimum score to report a hit (default: 110). |
| `--debug_slot` | Debugging parameter for specific slot monitoring. |
| `--slow_output` | artificial delay for testing UI responsiveness. |

## Architecture
The host code (`metal_sw.mm`) manages data loading, Metal buffer allocation, and kernel dispatch. The shader code (`sw.metal`) performs the actual alignment on the GPU.
