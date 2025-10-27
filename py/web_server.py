from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
from typing import Dict, Any
import logging

from .job_manager import JobManager
from .computation import run_computation

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global job manager
job_manager = JobManager()

# REST endpoints
@app.get("/api/jobs")
async def list_jobs():
    """List all jobs and their statuses"""
    return job_manager.list_jobs()

@app.get("/api/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status for a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.get_state()

@app.get("/api/job/{job_id}/statistics")
async def get_job_statistics(job_id: str):
    """Get detailed statistics for a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    state = job.get_state()
    return {
        "job_id": job_id,
        "score_statistics": state.get("score_statistics", {}),
        "bridges_found": state.get("bridges_found", 0),
        "memory_usage_mb": state.get("memory_usage_mb", 0),
        "gpu_memory_mb": state.get("gpu_memory_mb", 0),
        "last_update": state.get("last_update")
    }

@app.post("/api/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a specific job"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.update(status="cancelling")
    return {"job_id": job_id, "status": "cancelling"}

@app.post("/api/start_computation")
async def start_computation_endpoint(config: Dict[str, Any] = None):
    """Start a new computation job"""
    job_id = job_manager.create_job()
    job = job_manager.get_job(job_id)
    
    # Start in background thread
    threading.Thread(target=run_computation, args=(job, config), daemon=True).start()
    
    return {"job_id": job_id, "status": "started"}

# Serve a simple test page
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting REST server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")