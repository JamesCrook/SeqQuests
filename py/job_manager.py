import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Type
import logging

# Import job functions
from computation import run_computation
from data_munger import run_data_munging
from seq_search import run_seq_search
from nws_search import run_nws_search
from sequences import read_dat_records

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
            "sequences_examined": 0,
            "most_recent_item": "",
            "last_ten_accepted": [],
            "proteins_processed": 0,
        })

    def run(self):
        logger.info(f"Running data munging job {self.job_id} with config {self.state['config']}")
        try:
            config = self.state['config']
            run_data_munging(
                organisms=config.get('organisms', []),
                require_go=config.get('require_go', False),
                require_ec=config.get('require_ec', False),
                require_pfam=config.get('require_pfam', False),
                job=self
            )
            if self.state['status'] != 'cancelled':
                self.update(status="completed")
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])
        logger.info(f"Data munging job {self.job_id} finished.")


from nws import FastNwsDummy, FastNWS

class SequenceSearchJob(Job):
    def __init__(self, job_id: str):
        super().__init__(job_id, "sequence_search")
        self.state.update({
            "accession": "",
            "sequences_examined": 0,
            "most_recent_item": "",
            "last_ten_accepted": [],
        })

    def run(self):
        logger.info(f"Running sequence search job {self.job_id} with config {self.state['config']}")
        try:
            config = self.state['config']
            run_seq_search(
                identifier=config.get('accession'),
                use_fastnws=config.get('use_fastnws', False),
                job=self
            )
            if self.state['status'] != 'cancelled':
                self.update(status="completed")
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])
        logger.info(f"Sequence search job {self.job_id} finished.")


class NwsSearchJob(Job):
    def __init__(self, job_id: str):
        super().__init__(job_id, "nws_search")
        self.state.update({
            "output_log": [],
        })

    def run(self):
        logger.info(f"Running NWS search job {self.job_id} with config {self.state['config']}")
        try:
            config = self.state['config']
            run_nws_search(
                job=self,
                debug_slot=config.get('debug_slot', -1),
                reporting_threshold=config.get('reporting_threshold', 110),
                start_at=config.get('start_at', 0),
                num_seqs=config.get('num_seqs', 1),
                slow_output=config.get('slow_output', False),
                pam_data=config.get('pam_data', "c_src/pam250.bin"),
                fasta_data=config.get('fasta_data', "c_src/fasta.bin"),
            )
            if self.state['status'] != 'cancelled':
                self.update(status="completed")
        except Exception as e:
            logger.error(f"Job {self.job_id} failed: {e}")
            self.update(status="failed", errors=[str(e)])
        logger.info(f"NWS search job {self.job_id} finished.")


JOB_TYPES = {
    "computation": ComputationJob,
    "data_munging": DataMungingJob,
    "sequence_search": SequenceSearchJob,
    "nws_search": NwsSearchJob,
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
