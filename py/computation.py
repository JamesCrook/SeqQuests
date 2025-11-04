import time
import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from job_manager import Job

"""
This is a dummy job for the task runner framework.
It makes up fake statistic scores to report.
"""    

logger = logging.getLogger(__name__)

def run_computation(job: "Job", config: Dict[str, Any] = None):
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
            while job.get_state()['status'] == 'paused':
                time.sleep(1)
            # Check if cancelled
            if job.get_state()["status"] == "cancelling":
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
            errors=job.get_state()["errors"] + [str(e)]
        )