# Web Server Documentation

## Overview
`web_server.py` is a FastAPI-based web server that provides the user interface and API for the project. It serves static HTML/JS/CSS files and exposes endpoints for job management (create, start, stop, configure, monitor).

## Usage

```bash
python py/web_server.py
```

## Command Line Arguments
| Argument | Description |
|----------|-------------|
| `--test` | Run a test stub instead of starting the server. |

## API Endpoints
* `GET /`: Serve main UI.
* `GET /api/job_types`: List available job types.
* `GET /api/jobs`: List current jobs.
* `POST /api/job`: Create a job.
* `POST /api/job/{id}/start`: Start a job.
* `POST /api/job/{id}/pause`: Pause a job.
* `POST /api/job/{id}/resume`: Resume a job.
* `DELETE /api/job/{id}`: Delete a job.
* `POST /api/job/{id}/configure`: Configure a job.
* `GET /api/findings`: Get results file.
* `GET /stream-data`: Stream results CSV.

## Static Files
Served from `/static`.
