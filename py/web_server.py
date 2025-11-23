from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from typing import Dict, Any
import logging
from pydantic import BaseModel

from job_manager import JobManager, JOB_TYPES
import sequences
import os
from pathlib import Path

"""
FastAPI web server acting as a thin wrapper over the raw job functions and static html.
Through the website so exposed we can start, configure, stop and monitor jobs.
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FINDINGS_FILE = Path("./nws_results/finds.txt")  # Path to your main results file


# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global job manager
job_manager = JobManager()

# Pydantic models for request bodies
class JobCreationRequest(BaseModel):
    job_type: str

class JobConfigRequest(BaseModel):
    config: Dict[str, Any]

# --- REST Endpoints ---

@app.get("/api/job_types")
async def get_job_types():
    """Return a list of available job types."""

    return [{"id": job["id"], "display_name": job["display_name"]} for job in JOB_TYPES]

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs and their statuses."""
    return job_manager.list_jobs()

@app.post("/api/job")
async def create_job_endpoint(request: JobCreationRequest):
    """Create a new job of a specific type."""
    job_id = job_manager.create_job(request.job_type)
    if not job_id:
        raise HTTPException(status_code=400, detail=f"Invalid job type: {request.job_type}")
    return {"job_id": job_id, "status": "created"}

@app.get("/api/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status for a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.get_state()

@app.post("/api/job/{job_id}/start")
async def start_job(job_id: str):
    """Start a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.start()
    return {"job_id": job_id, "status": "starting"}

@app.post("/api/job/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.pause()
    return {"job_id": job_id, "status": "pausing"}

@app.post("/api/job/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.resume()
    return {"job_id": job_id, "status": "resuming"}

@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.delete()
    return {"job_id": job_id, "status": "deleting"}

@app.post("/api/job/{job_id}/configure")
async def configure_job(job_id: str, request: JobConfigRequest):
    """Configure a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.configure(request.config)
    return {"job_id": job_id, "status": "configured"}

@app.get("/api/proteins")
async def get_proteins():
    """Return the first 20 proteins from the FASTA file."""
    protein_iterator = sequences.read_fasta_sequences()
    proteins = []
    for _ in range(20):
        try:
            record = next(protein_iterator)
            proteins.append((record.description, str(record.seq)))
        except StopIteration:
            break
    return proteins

@app.get("/api/findings", response_class=PlainTextResponse)
async def get_findings():
    """Return the findings file content"""
    if not FINDINGS_FILE.exists():
        raise HTTPException(status_code=404, detail="Findings file not found")
    
    try:
        return FINDINGS_FILE.read_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading findings: {str(e)}")

@app.get("/api/sequence/{identifier}")
async def get_sequence(identifier: str):
    """Get a single protein sequence by accession number or index."""
    sequence_iterator = sequences.read_fasta_sequences()
    if identifier.isdigit():
        sequence_data = sequences.get_sequence_by_identifier(int(identifier), sequence_iterator)
    else:
        sequence_data = sequences.get_sequence_by_identifier(identifier, sequence_iterator)

    if not sequence_data:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return {"header": sequence_data[0], "sequence": sequence_data[1]}

# --- Web UI Routes ---

@app.get("/")
async def read_root():
    """Serve the main index page."""
    return FileResponse('static/match_explorer.html')

@app.get("/jobs")
async def read_jobs():
    """Serve the job selection page."""
    return FileResponse('static/jobs.html')

@app.get("/config/{job_type}")
async def get_config_page(job_type: str):
    """Serve the configuration page for a given job type."""
    page_path = f'static/config_{job_type}.html'
    try:
        return FileResponse(page_path)
    except RuntimeError:
        # This will happen if the file does not exist.
        raise HTTPException(status_code=404, detail="Configuration page not found")

async def stream_file(filepath: str, chunk_size: int = 8192):
    """Stream file in chunks"""
    with open(filepath, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
            # Optional: allow other tasks to run
            await asyncio.sleep(0)

@app.get("/stream-data")
async def stream_data():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(project_root, 'nws_results', 'results.csv')
    return StreamingResponse(
        stream_file(filepath),
        media_type="text/plain"
    )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting REST server on http://localhost:8000")
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000)