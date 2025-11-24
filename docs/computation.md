# Computation Module Documentation

## Overview
The `computation.py` module contains logic for running computational jobs, specifically designed as a dummy/simulation job for testing the job runner framework.

## Usage
This module is typically imported and used by `job_manager.py`. It can also be run directly for testing.

```bash
python py/computation.py --test
```

## Settings
When running as a job, it accepts the following configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_proteins` | int | 1000 | The number of proteins to simulate processing. |

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--test` | Run a simple test stub to verify the module loads correctly. |
