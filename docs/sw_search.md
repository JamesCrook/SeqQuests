# SW Search Documentation

## Overview
`sw_search.py` is a Python wrapper around the high-performance Metal (GPU) Smith-Waterman search executable. It manages the execution, monitors output, and handles long-running search jobs.

Unlike the underlying executable, the wrapper will resume a search buy looking at the tail of the output file to dewtermine what sequence to start with.

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


