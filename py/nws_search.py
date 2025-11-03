import subprocess
import logging
from collections import deque

logger = logging.getLogger(__name__)

def run_nws_search(
    job,
    debug_slot: int = -1,
    reporting_threshold: int = 110,
    start_at: int = 0,
    num_seqs: int = 1,
    slow_output: bool = False,
    pam_data: str = "c_src/pam250.bin",
    fasta_data: str = "c_src/fasta.bin",
):
    """
    This function will wrap the metal_nws.mm executable and monitor its output.
    """
    # For testing, we'll use the dummy script. In a real scenario, this would
    # be the path to the compiled metal_nws.mm executable.
    executable_path = "./bin/dummy_nws_search"

    args = [
        executable_path,
        "--debug_slot", str(debug_slot),
        "--reporting_threshold", str(reporting_threshold),
        "--start_at", str(start_at),
        "--num_seqs", str(num_seqs),
        "--pam_data", pam_data,
        "--fasta_data", fasta_data,
    ]
    if slow_output:
        args.append("--slow_output")

    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    output_log = deque(maxlen=10)

    for line in iter(process.stdout.readline, ''):
        if job.get_state()['status'] == 'cancelled':
            process.terminate()
            break

        line = line.strip()
        if line:
            output_log.append(line)
            job.update(output_log=list(output_log))

    process.stdout.close()
    return_code = process.wait()

    if return_code != 0:
        logger.error(f"NWS search job {job.job_id} failed with return code {return_code}")
        job.update(status="failed", errors=[f"Process exited with code {return_code}"])
