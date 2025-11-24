# Data Munger Documentation

## Overview
`data_munger.py` is responsible for filtering and processing Swiss-Prot protein data. It reads sequences, applies filters (like organism, GO terms, EC numbers), and outputs the results.

## Usage
Can be run as a standalone script or as a job.

```bash
python py/data_munger.py [options]
```

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--organisms` | List of organisms to include (e.g., `human`, `mouse`, `rat`, `ecoli`). |
| `--require-go` | Only include proteins with Gene Ontology (GO) terms. |
| `--require-ec` | Only include proteins with Enzyme Commission (EC) numbers. |
| `--require-pfam` | Only include proteins with Pfam domains. |
| `--test` | Run the internal test function (filtering for mouse). |

## Job Configuration
When running as a job, the configuration dictionary matches the command line arguments:
* `organisms`: List[str]
* `require_go`: bool
* `require_ec`: bool
* `require_pfam`: bool
