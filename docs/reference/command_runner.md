# Command Runner Module Documentation

## Overview
The `command_runner.py` module contains logic for running and capturing output from some other job. The current state of a job can be obtained by interrogating CommandRunner.

The central idea is that it acts as a wrapper over any long running task, capturing and sorting output strings, providing start/pause/resume/delete funcionality and ongoing monitoring.

## Usage
This module is typically imported and used by `job_manager.py`. It can also be run directly for testing.

```bash
python py/commmand_runner.py --test
```

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--test` | Run a simple test stub to verify the module loads correctly. |
