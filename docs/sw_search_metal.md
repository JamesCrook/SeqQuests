# SW Search Metal Documentation

## Overview
`sw_search_metal` (compiled from `c_src/sw_search_metal.mm` and `c_src/sw.metal`) is the core high-performance compute engine. It uses Apple's Metal API to perform Smith-Waterman local alignment on the GPU.

It returns scores, but not the actual alignments.

## Usage

```bash
./bin/sw_search_metal [options]
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
| `--slow_output` | artificial delay so that we can see responses. |

## Architecture
The host code (`sw_search_metal.mm`) manages data loading, Metal buffer allocation, and kernel dispatch. The shader code (`sw.metal`) performs the actual alignment on the GPU.

## Job Configuration UI
When running as a job (`SwSearchJob`), the UI allows configuration of the exact same parameters:
* `pam_data`: str (Path to PAM matrix binary file)
* `fasta_data`: str (Path to FASTA database binary file)
* `start_at`: int (Sequence index to start at)
* `num_seqs`: int (Number of sequences to process)
* `reporting_threshold`: int (Score threshold for reporting hits)
* `debug_slot`: int (Debug parameter for the Metal kernel)
* `slow_output`: bool (If true, slows down output for debugging)
