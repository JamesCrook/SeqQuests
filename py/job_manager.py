import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Type
import logging

# Import job functions
from computation import run_computation
from data_munger import filter_proteins
from sequences import read_dat_records, read_fasta_sequences

logger = logging.getLogger(__name__)

class Job:
    def __init__(self, job_id: str, job_type: str):
        self.job_id = job_id
        self.job_type = job_type
        self.state = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "paused",
            "config": {},
            "current_step": "Created",
            "start_time": None,
            "elapsed_time": 0,
            "errors": [],
            "last_update": datetime.utcnow().isoformat()
        }
        self.lock = threading.Lock()
        self.thread = None

    def update(self, **kwargs):
        with self.lock:
            self.state.update(kwargs)
            self.state["last_update"] = datetime.utcnow().isoformat()

            if self.state["start_time"]:
                self.state["elapsed_time"] = time.time() - self.state["start_time"]

    def get_state(self):
        with self.lock:
            return self.state.copy()

    def start(self):
        if self.state['status'] not in ['paused', 'created']:
            logger.warning(f"Job {self.job_id} cannot be started from state {self.state['status']}")
            return

        self.update(status="running", start_time=time.time())
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        logger.info(f"Job {self.job_id} started.")

    def pause(self):
        if self.state['status'] != 'running':
            logger.warning(f"Job {self.job_id} cannot be paused from state {self.state['status']}")
            return

        self.update(status="paused")
        logger.info(f"Job {self.job_id} paused.")

    def resume(self):
        if self.state['status'] != 'paused':
            logger.warning(f"Job {self.job_id} cannot be resumed from state {self.state['status']}")
            return

        self.update(status="running")
        logger.info(f"Job {self.job_id} resumed.")

    def cancel(self):
        self.update(status="cancelled")
        logger.info(f"Job {self.job_id} cancelled.")

    def configure(self, config: Dict[str, Any]):
        with self.lock:
            self.state['config'].update(config)
        logger.info(f"Job {self.job_id} configured.")

    def run(self):
        raise NotImplementedError("Subclasses must implement the run method")


class ComputationJob(Job):
    def __init__(self, job_id: str):
        super().__init__(job_id, "computation")
        self.state.update({
            "total_proteins": 0,
            "processed_pairs": 0,
            "total_pairs": 0,
            "current_batch": 0,
            "total_batches": 0,
            "score_statistics": {},
            "bridges_found": 0,
            "memory_usage_mb": 0,
            "gpu_memory_mb": 0,
        })

    def run(self):
        try:
            run_computation(self, self.state.get('config'))
            if self.state['status'] != 'cancelled':
                self.update(status="completed")
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])


class DataMungingJob(Job):
    def __init__(self, job_id: str):
        super().__init__(job_id, "data_munging")
        self.state.update({
            "filtered_organisms": 0,
            "proteins_processed": 0,
        })

    def run(self):
        logger.info(f"Running data munging job {self.job_id} with config {self.state['config']}")
        try:
            organisms = self.state['config'].get('organisms', [])
            all_records = read_dat_records()
            filtered_records = filter_proteins(all_records, organisms=organisms)

            count = 0
            for _ in filtered_records:
                while self.state['status'] == 'paused':
                    time.sleep(1)
                if self.state['status'] == 'cancelled':
                    break
                count += 1
                self.update(proteins_processed=count)

            if self.state['status'] != 'cancelled':
                self.update(status="completed", filtered_organisms=count)
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])
        logger.info(f"Data munging job {self.job_id} finished.")


class SequenceSearchJob(Job):
    def __init__(self, job_id: str):
        super().__init__(job_id, "sequence_search")
        self.state.update({
            "query_sequence": "",
            "matches_found": 0,
        })

    def run(self):
        logger.info(f"Running sequence search job {self.job_id} with config {self.state['config']}")
        try:
            query_sequence = self.state['config'].get('query_sequence')
            if not query_sequence:
                raise ValueError("Query sequence not specified.")

            all_sequences = read_fasta_sequences()
            matches = 0
            for header, sequence in all_sequences:
                while self.state['status'] == 'paused':
                    time.sleep(1)
                if self.state['status'] == 'cancelled':
                    break
                if query_sequence in sequence:
                    matches += 1
                    self.update(matches_found=matches)

            if self.state['status'] != 'cancelled':
                self.update(status="completed")
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])
        logger.info(f"Sequence search job {self.job_id} finished.")


JOB_TYPES = {
    "computation": ComputationJob,
    "data_munging": DataMungingJob,
    "sequence_search": SequenceSearchJob,
}

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()

    def create_job(self, job_type: str) -> Optional[str]:
        job_id = str(uuid.uuid4())
        job_class = JOB_TYPES.get(job_type)

        if not job_class:
            logger.error(f"Unknown job type: {job_type}")
            return None

        with self.lock:
            self.jobs[job_id] = job_class(job_id)

        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self) -> Dict[str, Any]:
        with self.lock:
            return {
                job_id: {
                    "status": job.state["status"],
                    "job_type": job.job_type,
                    "created_at": job.state["last_update"]
                }
                for job_id, job in self.jobs.items()
            }