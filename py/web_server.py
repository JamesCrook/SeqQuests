from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

import asyncio
from typing import Dict, Any
import logging
from pydantic import BaseModel
import argparse
import json

from job_manager import JobManager, JOB_TYPES
import sequences
import sw_align
import os
from pathlib import Path
import re


"""
FastAPI web server acting as a thin wrapper over the raw job functions and static html.
Through the website so exposed we can start, configure, stop and monitor jobs.
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Remove when debugging is complete.
app.add_middleware(NoCacheMiddleware)

FINDINGS_FILE = PROJECT_ROOT / "sw_results" / "sw_finds.txt"  # Path to your main results file


# Mount static files directory
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")

# Global job manager
job_manager = JobManager()

# Pydantic models for request bodies
class JobCreationRequest(BaseModel):
    job_type: str

class JobConfigRequest(BaseModel):
    config: Dict[str, Any]

# Only allow safe filename characters
SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._\-]*$')

def safe_filename(filename: str) -> str:
    """
    Validate filename contains only safe characters.
    Allowlist approach: alphanumeric, dots, dashes, underscores.
    Must start with alphanumeric (prevents dotfiles and hidden files).
    """
    if not filename or not SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return filename

# --- REST Endpoints ---
""" The order in which these functions appear determines the order in 
the API /docs, so take some care to group and order the items logically.
"""


@app.get("/api/job_types")
async def get_job_types():
    """Return a list of available job types."""

    return [{"id": job["id"], "display_name": job["display_name"]} for job in JOB_TYPES]


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs and their statuses."""
    return job_manager.list_jobs()

@app.get("/api/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status for a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.get_state()

@app.post("/api/job")
async def create_job_endpoint(request: JobCreationRequest):
    """Create a new job of a specific type."""
    job_id = job_manager.create_job(request.job_type)
    if not job_id:
        raise HTTPException(status_code=400, detail=f"Invalid job type: {request.job_type}")
    return {"job_id": job_id, "status": "created"}

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

@app.post("/api/job/{job_id}/configure")
async def configure_job(job_id: str, request: JobConfigRequest):
    """Configure a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.configure(request.config)
    return {"job_id": job_id, "status": "configured"}

@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.delete()
    return {"job_id": job_id, "status": "deleting"}

@app.get("/api/findings", response_class=PlainTextResponse)
async def get_findings():
    """Return the findings file content"""
    if not FINDINGS_FILE.exists():
        raise HTTPException(status_code=404, detail="Findings file not found")
    
    try:
        return FINDINGS_FILE.read_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading findings: {str(e)}")

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

# Provides an API to the links data as a stream of data  
@app.get("/stream-data")
async def stream_link_data():
    filepath = PROJECT_ROOT / 'sw_results' / 'sw_results.csv'
    return StreamingResponse(
        stream_file(str(filepath)),
        media_type="text/plain"
    )

@app.get("/api/comparison/{id1}/{id2}")
async def get_sequence_alignment(id1: str, id2: str):
    s1 = sequences.get_protein( int(id1) )
    s2 = sequences.get_protein( int(id2) )
    alignment = sw_align.align_local_swissprot( s1.full.sequence, s2.full.sequence)

    parts = alignment['visual_text'].split('\n')
    return {
        "sequence1": s1.full.raw,
        "sequence2": s2.full.raw,
        "score": alignment['score'],
        "alignment1": parts[0],
        "alignment2": parts[2],
        "matches": parts[1],
        "seq1_start": alignment['range_summary']['seq_a_start'],  # 0-indexed
        "seq2_start": alignment['range_summary']['seq_b_start'],  # 0-indexed
    }

@app.get("/api/proteins")
async def get_sequences():
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

@app.get("/api/sequence/{identifier}")
async def get_sequence(identifier: str):
    """Get a single protein sequence by accession number or index."""
    if identifier.isdigit():
        sequence_data = sequences.get_protein(int(identifier))
        if not sequence_data:
            raise HTTPException(status_code=404, detail="Sequence not found")
        return {"header": sequence_data.name, "sequence": sequence_data.full.sequence}
    else:
        sequence_iterator = sequences.read_fasta_sequences()
        sequence_data = sequences.get_sequence_by_identifier(identifier, sequence_iterator)

    if not sequence_data:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return {"header": sequence_data.description, "sequence": str( sequence_data.seq )}

# --- Web UI Routes ---


def _get_doc_list() -> list:
    """Get list of available documentation files."""
    docs_path = PROJECT_ROOT / "static/docs"
    if not docs_path.exists():
        return []
    docs = []
    for file in docs_path.glob("*.md"):
        docs.append({
            "name": file.stem.replace("_", " ").title(),
            "filename": file.name
        })
    return sorted(docs, key=lambda x: x['name'])

@app.get("/api/docs")
async def list_docs():
    """List available documentation files."""
    return _get_doc_list()

@app.get("/docs/doclist.js")
async def get_document_list():
    """Serve the document list, updating the file only if it has changed."""
    docs_path = PROJECT_ROOT / "static/docs"
    doclist_path = docs_path / "doclist.js"
    
    # Get current docs and generate JS content
    docs = _get_doc_list()
    docs_json = json.dumps(docs, indent=2)
    new_content = f'{docs_json}'
    
    # Read existing file if it exists
    existing_content = ""
    if doclist_path.exists():
        existing_content = doclist_path.read_text()
    
    # Update file only if content has changed
    if new_content != existing_content:
        doclist_path.parent.mkdir(parents=True, exist_ok=True)
        doclist_path.write_text(new_content)
        logger.info("Updated doclist.js")
    
    return FileResponse(doclist_path, media_type="application/javascript")

@app.get("/")
async def read_root():
    """Serve the main index page."""
    return FileResponse(PROJECT_ROOT / 'static/lcars.html')

@app.get("/favicon.ico")
async def get_favicon():
    """Serve the job selection page."""
    return FileResponse(PROJECT_ROOT / 'static/wheel.ico')

@app.get("/{page}")
async def read_page(page: str):
    page = safe_filename(page)
    return FileResponse(PROJECT_ROOT / f'static/{page}')

@app.get("/panels/{file}")
async def get_part_for_html_page(file: str):
    file = safe_filename(file)
    return FileResponse(PROJECT_ROOT / f'static/panels/{file}')

@app.get("/docs/{file}")
async def get_document(file: str):
    file = safe_filename(file)
    file_path = PROJECT_ROOT / "static/docs" / file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI Web Server")
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to bind the server to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8006,
                        help='Port to bind the server to (default: 8002)')
    parser.add_argument('--reload', action='store_true',
                        help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1,
                        help='Number of worker processes (default: 1)')
    parser.add_argument('--log-level', type=str, 
                        choices=['critical', 'error', 'warning', 'info', 'debug'],
                        default='info',
                        help='Logging level (default: info)')
    
    args = parser.parse_args()
    
    import uvicorn
    logger.info(f"Starting REST server on http://{args.host}:{args.port}")
    uvicorn.run(
        "web_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # reload only works with 1 worker
        log_level=args.log_level
    )
