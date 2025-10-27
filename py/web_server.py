from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from pydantic import BaseModel

from job_manager import JobManager
from sequences import read_fasta_sequences

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/api/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.cancel()
    return {"job_id": job_id, "status": "cancelling"}

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
    proteins = read_fasta_sequences()
    return proteins[:20]

# --- Web UI Routes ---

@app.get("/")
async def read_root():
    """Serve the main index page."""
    return FileResponse('static/index.html')

@app.get("/config/{job_type}")
async def get_config_page(job_type: str):
    """Serve the configuration page for a given job type."""
    page_path = f'static/config_{job_type}.html'
    try:
        return FileResponse(page_path)
    except RuntimeError:
        # This will happen if the file does not exist.
        raise HTTPException(status_code=404, detail="Configuration page not found")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting REST server on http://localhost:8000")
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000)