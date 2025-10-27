from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

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

# Job storage - in production, use a database
class JobManager:
    def __init__(self):
        self.jobs = {}  # job_id -> ProgressMonitor
        self.lock = threading.Lock()
    
    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        with self.lock:
            self.jobs[job_id] = ProgressMonitor(job_id)
        return job_id
    
    def get_job(self, job_id: str) -> Optional['ProgressMonitor']:
        with self.lock:
            return self.jobs.get(job_id)
    
    def list_jobs(self) -> Dict[str, str]:
        with self.lock:
            return {job_id: job.state["status"] for job_id, job in self.jobs.items()}

# Progress state per job
class ProgressMonitor:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.state = {
            "job_id": job_id,
            "status": "idle",
            "current_step": "",
            "total_proteins": 0,
            "processed_pairs": 0,
            "total_pairs": 0,
            "current_batch": 0,
            "total_batches": 0,
            "start_time": None,
            "elapsed_time": 0,
            "estimated_remaining": 0,
            "score_statistics": {},
            "bridges_found": 0,
            "memory_usage_mb": 0,
            "gpu_memory_mb": 0,
            "errors": [],
            "last_update": datetime.utcnow().isoformat()
        }
        self.lock = threading.Lock()
        
    def update(self, **kwargs):
        with self.lock:
            self.state.update(kwargs)
            self.state["last_update"] = datetime.utcnow().isoformat()
            
            if self.state["start_time"]:
                self.state["elapsed_time"] = time.time() - self.state["start_time"]
            
            # Calculate estimated time remaining
            if self.state["total_pairs"] > 0 and self.state["processed_pairs"] > 0:
                rate = self.state["processed_pairs"] / self.state["elapsed_time"]
                remaining = self.state["total_pairs"] - self.state["processed_pairs"]
                self.state["estimated_remaining"] = remaining / rate if rate > 0 else 0
    
    def get_state(self):
        with self.lock:
            return self.state.copy()

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
async def start_computation(config: Dict[str, Any] = None):
    """Start a new computation job"""
    job_id = job_manager.create_job()
    job = job_manager.get_job(job_id)
    
    def run_computation():
        try:
            n_proteins = config.get("n_proteins", 1000) if config else 1000
            total_pairs = n_proteins * (n_proteins + 1) // 2
            
            job.update(
                status="computing",
                current_step="Initializing",
                total_proteins=n_proteins,
                total_pairs=total_pairs,
                processed_pairs=0,
                start_time=time.time()
            )
            
            # Simulate computation
            for i in range(100):
                # Check if cancelled
                if job.state["status"] == "cancelling":
                    job.update(
                        status="cancelled",
                        current_step="Computation cancelled"
                    )
                    return
                
                # Simulate progress
                processed = int((i + 1) / 100 * total_pairs)
                job.update(
                    processed_pairs=processed,
                    current_batch=i + 1,
                    total_batches=100,
                    memory_usage_mb=100 + i * 5,
                    gpu_memory_mb=200 + i * 10,
                    score_statistics={
                        "min": -50.0 + i * 0.1,
                        "max": 200.0 - i * 0.5,
                        "mean": 25.0 + i * 0.2,
                    },
                    bridges_found=i // 10,
                    current_step=f"Processing batch {i+1}/100"
                )
                
                time.sleep(0.1)  # Simulate work
            
            job.update(
                status="completed",
                current_step="Analysis complete"
            )
            
        except Exception as e:
            logger.error(f"Error in computation: {e}")
            job.update(
                status="error",
                current_step=f"Error: {str(e)}",
                errors=job.state["errors"] + [str(e)]
            )
    
    # Start in background thread
    threading.Thread(target=run_computation, daemon=True).start()
    
    return {"job_id": job_id, "status": "started"}

# Serve a simple test page
@app.get("/")
async def read_root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protein Analysis Monitor (REST)</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #status { font-weight: bold; }
            #progress { margin: 20px 0; }
            button { margin: 5px; padding: 10px; }
            .stat { margin: 5px 0; }
            .error { color: red; }
            .success { color: green; }
            .job-item { 
                padding: 10px; 
                margin: 5px 0; 
                background: #e8e8e8; 
                cursor: pointer; 
                border-radius: 5px;
            }
            .job-item:hover { background: #d0d0d0; }
            .active-job { background: #c0e0c0; }
            #pollControl {
                margin: 10px 0;
                padding: 10px;
                background: #f0f0f0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>Protein Similarity Analysis Monitor (REST/Polling)</h1>
        
        <div>
            <button onclick="startComputation()">Start New Computation</button>
            <button onclick="cancelComputation()">Cancel Current Job</button>
            <button onclick="refreshJobs()">Refresh Jobs</button>
        </div>
        
        <div id="pollControl">
            <label>Poll Interval: 
                <select id="pollInterval" onchange="updatePollInterval()">
                    <option value="0">Manual Only</option>
                    <option value="500">0.5 seconds</option>
                    <option value="1000" selected>1 second</option>
                    <option value="5000">5 seconds</option>
                    <option value="10000">10 seconds</option>
                    <option value="30000">30 seconds</option>
                </select>
            </label>
            <span id="pollStatus" style="margin-left: 20px;">Polling: Active</span>
        </div>
        
        <div id="jobList" style="margin: 20px 0;">
            <h3>Jobs</h3>
            <div id="jobs"></div>
        </div>
        
        <div id="currentJob">
            <h3>Current Job: <span id="currentJobId">None</span></h3>
            <div id="status">Status: <span id="statusText">-</span></div>
            <div id="currentStep">Step: <span id="stepText">-</span></div>
            
            <div id="progress">
                <div class="stat">Proteins: <span id="proteins">0</span></div>
                <div class="stat">Progress: <span id="pairs">0</span> / <span id="totalPairs">0</span> pairs</div>
                <div class="stat">Time: <span id="elapsed">0</span>s (remaining: <span id="remaining">0</span>s)</div>
                <div class="stat">Memory: CPU <span id="cpuMem">0</span>MB, GPU <span id="gpuMem">0</span>MB</div>
                <div class="stat">Bridges found: <span id="bridges">0</span></div>
                <div class="stat">Last Update: <span id="lastUpdate">-</span></div>
            </div>
        </div>
        
        <div id="log" style="margin-top: 20px; padding: 10px; background: #f0f0f0; height: 200px; overflow-y: auto;">
            <h3>Log</h3>
        </div>
        
        <script>
            let currentJobId = null;
            let pollTimer = null;
            let pollInterval = 1000;
            const log = document.getElementById('log');
            
            function addLog(message, type = '') {
                const timestamp = new Date().toLocaleTimeString();
                const className = type ? ` class="${type}"` : '';
                log.innerHTML += `<p${className}>[${timestamp}] ${message}</p>`;
                log.scrollTop = log.scrollHeight;
            }
            
            function updatePollInterval() {
                const select = document.getElementById('pollInterval');
                pollInterval = parseInt(select.value);
                
                // Clear existing timer
                if (pollTimer) {
                    clearTimeout(pollTimer);
                    pollTimer = null;
                }
                
                // Update status
                document.getElementById('pollStatus').textContent = 
                    pollInterval === 0 ? 'Polling: Disabled' : `Polling: Every ${pollInterval/1000}s`;
                
                // Restart polling if enabled
                if (pollInterval > 0 && currentJobId) {
                    pollJobStatus();
                }
                
                addLog(`Poll interval set to ${pollInterval}ms`);
            }
            
            async function refreshJobs() {
                try {
                    const response = await fetch('/api/jobs');
                    const jobs = await response.json();
                    
                    const jobsDiv = document.getElementById('jobs');
                    jobsDiv.innerHTML = '';
                    
                    Object.entries(jobs).forEach(([jobId, status]) => {
                        const div = document.createElement('div');
                        div.className = 'job-item' + (jobId === currentJobId ? ' active-job' : '');
                        div.innerHTML = `${jobId.substring(0, 8)}... - ${status}`;
                        div.onclick = () => selectJob(jobId);
                        jobsDiv.appendChild(div);
                    });
                    
                    addLog('Jobs list refreshed');
                } catch (e) {
                    addLog(`Failed to refresh jobs: ${e}`, 'error');
                }
            }
            
            function selectJob(jobId) {
                currentJobId = jobId;
                document.getElementById('currentJobId').textContent = jobId.substring(0, 12) + '...';
                addLog(`Selected job: ${jobId}`);
                refreshJobs();
                pollJobStatus();
            }
            
            async function pollJobStatus() {
                if (!currentJobId) return;
                
                try {
                    const response = await fetch(`/api/job/${currentJobId}/status`);
                    if (!response.ok) {
                        if (response.status === 404) {
                            addLog('Job not found', 'error');
                            currentJobId = null;
                            return;
                        }
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    updateDisplay(data);
                    
                    // Continue polling if job is active and interval is set
                    if (pollInterval > 0 && 
                        ['computing', 'initializing'].includes(data.status)) {
                        pollTimer = setTimeout(pollJobStatus, pollInterval);
                    }
                } catch (e) {
                    addLog(`Failed to poll status: ${e}`, 'error');
                }
            }
            
            function updateDisplay(data) {
                document.getElementById('statusText').textContent = data.status;
                document.getElementById('stepText').textContent = data.current_step || '-';
                document.getElementById('proteins').textContent = data.total_proteins;
                document.getElementById('pairs').textContent = data.processed_pairs;
                document.getElementById('totalPairs').textContent = data.total_pairs;
                document.getElementById('elapsed').textContent = Math.round(data.elapsed_time);
                document.getElementById('remaining').textContent = Math.round(data.estimated_remaining);
                document.getElementById('cpuMem').textContent = Math.round(data.memory_usage_mb);
                document.getElementById('gpuMem').textContent = Math.round(data.gpu_memory_mb);
                document.getElementById('bridges').textContent = data.bridges_found;
                document.getElementById('lastUpdate').textContent = 
                    new Date(data.last_update).toLocaleTimeString();
            }
            
            async function startComputation() {
                try {
                    const response = await fetch('/api/start_computation', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            n_proteins: 1000,
                            batch_size: 100,
                            threshold: -20
                        })
                    });
                    const data = await response.json();
                    addLog(`Computation started: Job ID ${data.job_id}`, 'success');
                    selectJob(data.job_id);
                    refreshJobs();
                } catch (e) {
                    addLog(`Failed to start computation: ${e}`, 'error');
                }
            }
            
            async function cancelComputation() {
                if (!currentJobId) {
                    addLog('No job selected', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/job/${currentJobId}/cancel`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    addLog(`Cancel requested for job ${currentJobId}`);
                } catch (e) {
                    addLog(`Failed to cancel: ${e}`, 'error');
                }
            }
            
            // Initialize on load
            window.addEventListener('load', () => {
                addLog('Page loaded, REST API ready');
                refreshJobs();
            });
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting REST server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")