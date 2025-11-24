# SW Search Documentation

## Overview
`sw_search.py` is a Python wrapper around the high-performance Metal (GPU) Smith-Waterman search executable. It manages the execution, monitors output, and handles long-running search jobs.

## Usage

```bash
python py/sw_search.py [options]
```

## Command Line Arguments
| Argument | Default | Description |
|----------|---------|-------------|
| `--output_dir` | `sw_results` | Directory to store results. |
| `--flush_interval` | 60 | Seconds between flushing results to disk. |
| `--num_sequences` | 570000 | Total number of sequences in the database. |
| `--start_at` | Auto-detect | Sequence index to start/resume from. |
| `--test` | N/A | Run a test stub. |

## Job Configuration
When running as a job (`SwSearchJob`), it accepts:
* `debug_slot`: int (Debug parameter for the Metal kernel)
* `reporting_threshold`: int (Score threshold for reporting hits)
* `start_at`: int (Sequence index to start at)
* `num_seqs`: int (Number of sequences to process)
* `slow_output`: bool (If true, slows down output for debugging)
* `pam_data`: str (Path to PAM matrix binary file)
* `fasta_data`: str (Path to FASTA database binary file)
