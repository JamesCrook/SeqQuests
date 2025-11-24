# Command Runner Module Documentation

## Overview
The `command_runner.py` module contains logic for running and capturing output from some other job. The current state of a job can be obtained by interogating CommandRunner

## Usage
This module is typically imported and used by `job_manager.py`. It can also be run directly for testing.

```bash
python py/commmand_runner.py --test
```

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--test` | Run a simple test stub to verify the module loads correctly. |
