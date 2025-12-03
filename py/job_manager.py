import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Type
import logging
import argparse

# Import job functions
from computation import run_computation
from data_munger import run_data_munging
from sequences import read_swissprot_sequences
from command_runner import CommandRunner

from config import PROJECT_ROOT

"""
Classes for job management.
The JobManager can create list and delete jobs by id
Each job can start, pause, resume and provide status information
"""

logger = logging.getLogger(__name__)

class Job:
    def __init__(self, job_id: str, job_type: str, manager: 'JobManager'):
        self.job_id = job_id
        self.job_type = job_type
        self.manager = manager
        self.state = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "paused",
            "config": {},
            "current_step": "Created",
            "start_time": None,
            "elapsed_time": 0,
            "progress": "No Progress Info",
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

    def delete(self):
        self.update(status="cancelled")
        logger.info(f"Job {self.job_id} cancelled.")
        self.manager.delete_job(self.job_id)

    def configure(self, config: Dict[str, Any]):
        with self.lock:
            self.state['config'].update(config)
        logger.info(f"Job {self.job_id} configured.")

    def run(self):
        raise NotImplementedError("Subclasses must implement the run method")

class MockJob:
    def __init__(self):
        self.state = {"status": "running", "errors": []}
    
    def update(self, **kwargs):
        self.state.update(kwargs)
        # Print key updates for visibility
        if "current_step" in kwargs:
            print(f"  {kwargs['current_step']}")
        if "status" in kwargs and kwargs["status"] in ["completed", "error", "cancelled"]:
            print(f"  Final status: {kwargs['status']}")
    
    def get_state(self):
        return self.state

class ComputationJob(Job):
    def __init__(self, job_id: str, manager: 'JobManager'):
        super().__init__(job_id, "computation", manager)
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
    def __init__(self, job_id: str, manager: 'JobManager'):
        super().__init__(job_id, "data_munging", manager)
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


"""This is the proposed replacement version with enhnaced code 
for capturing command outputs.
"""
class SwSearchJob(Job):
    def __init__(self, job_id: str, manager: 'JobManager'):
        super().__init__(job_id, "sw_search", manager)
        self.state.update({
            "output_log": [],
            "bench":[],
            # Add buffered outputs
            "stats_buffer": [],
            "hits_buffer": [],
            "latest_stats": None,
            "latest_hit": None,
        })
    
    def run(self):
        config = self.state['config']
        
        executable = PROJECT_ROOT / "bin/sw_search_metal"
        command = [
            str(executable),
            f"--debug_slot",f"{config.get('debug_slot', -1)}",
            f"--reporting_threshold",f"{config.get('reporting_threshold', 130)}",
            f"--start_at",f"{config.get('start_at', 0)}",
            f"--num_seqs",f"{config.get('num_seqs', 600000)}",
            f"--pam_data",f"{config.get('pam_data', str(PROJECT_ROOT / 'data/pam250.bin'))}",
            f"--fasta_data",f"{config.get('fasta_data', str(PROJECT_ROOT / 'data/fasta.bin'))}"

        ]
    
        runner = CommandRunner(
            command,
            log_error_callback=lambda msg: self.update(errors=self.state['errors'] + [msg]),
            filter_prefixes={
                'stats': 'STATS:',
                'hits': 'HIT:',
                'bench': 'BENCH:',
                'seq': 'SEQ:',
                'step': 'STEP:'
            }
        )
        
        runner.start()
        
        for category, line in runner.read_output_filtered():
            # Update progress from stats
            #self.update(progress=line)
            if category == 'stats':
                self.update(progress=line)
            
            # Store hits
            elif category == 'hits':
                self.update(latest_hit=line)
            #print(f"::: {line}")
      
            # Handle pause/resume
            if self.state['status'] == 'paused':
                runner.pause()
                while self.state['status'] == 'paused':
                    time.sleep(0.5)
                runner.resume()
            
            if self.state['status'] == 'cancelled':
                runner.terminate()
                break

            buffers = runner.get_buffers()
            self.state['output_log'] = buffers.get('bench', [])
        
        # Sync final buffers to state
        buffers = runner.get_buffers()
        self.update(
            stats_buffer=buffers.get('stats', []),
            output_log=buffers.get('hits', [])
        )


JOB_TYPES = [
    {
        "id": "computation",
        "display_name": "Computation",
        "class": ComputationJob,
        "help": "A dummy computational job for testing the jobs framework",
    },
    {
        "id": "data_munging",
        "display_name": "Data Munging",
        "class": DataMungingJob,
        "help": "Job to create a filtered dataset. You configure what to filter. It does not yet write any files and is just for testing.",
    },
    {
        "id": "sw_search",
        "display_name": "Smith-Waterman Search",
        "class": SwSearchJob,
        "help": "Performs a full all-on-all swissprot to swissprot protein comparison, producing a csv file with high scoring links.",
    },
#    {
#        "id": "tree_builder",
#        "display_name": "Tree Builder",
#        "class": TreeBuilderJob,
#        "help": "Takes the high scoring links file and produces a maximal scoring tree of protein similarities. This is a massive data reduction O(N^2) -> O(N), keeping the best links between families of similar proteins. The retained lower scoring links may not be significant.",
#    },
#    {
#        "id": "prepare_binary_data",
#        "display_name": "Make Binary Data",
#        "class": BinaryDataJob,
#        "help": "A preparation step before sw searching, makes binary versions of PAM data and fastA data.",
#    },
#    {
#        "id": "check_fasta_data",
#        "display_name": "Is FastA OK",
#        "class": FastACheckJob,
#        "help": "Checks that the items in the FastA database correspond to the items in the SwissProt database."
#    },
]

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()

    def create_job(self, job_type: str) -> Optional[str]:
        job_id = str(uuid.uuid4())

        job_info = next((item for item in JOB_TYPES if item["id"] == job_type), None)

        if not job_info:
            logger.error(f"Unknown job type: {job_type}")
            return None

        job_class = job_info["class"]

        with self.lock:
            self.jobs[job_id] = job_class(job_id, self)

        logger.info(f"Created job {job_id} of type {job_type}")
        return job_id

    def delete_job(self, job_id: str):
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                logger.info(f"Deleted job {job_id}")

    def get_job(self, job_id: str) -> Optional[Job]:
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self) -> Dict[str, Any]:
        with self.lock:
            return {
                job_id: {
                    "status": job.state["status"],
                    "job_type": job.job_type,
                    "created_at": job.state["last_update"],
                    "progress": job.state["progress"]
                }
                for job_id, job in self.jobs.items()
            }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Manager module")
    parser.add_argument('--no-test', action='store_false', dest='test',
                        help='Disable test mode')
    parser.add_argument('--test', action='store_true', dest='test',
                        help='Enable test mode (default)')
    # Use from command line currently only for testing, so is the default
    parser.set_defaults(test=True)    
    args = parser.parse_args()

    if not args.test:
        parser.print_help()
        exit(0)

    """ Smoke test - will CommandRunner run? """
    print(f"Running in test mode...")
    # TODO: Make a CommandRunner and execute ls with it, ensuring it runs/terminates

