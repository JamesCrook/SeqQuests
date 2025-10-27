import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

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