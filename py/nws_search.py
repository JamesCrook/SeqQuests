import subprocess
import logging
from collections import deque
import signal
import os
import time
import pty
import select
import re

logger = logging.getLogger(__name__)


class MetalNWSRunner:
    def __init__(self, command):
        """
        Initialize the runner with the command to execute.

        Args:
            command: List of command arguments, e.g., ['./bin/metal_nws', 'query.fasta', 'database.fasta']
        """
        self.command = command
        self.process = None
        self.master_fd = None

    def start(self):
        """Start the metal_nws process using a pseudo-terminal for unbuffered output."""
        # Create a pseudo-terminal
        self.master_fd, slave_fd = pty.openpty()

        self.process = subprocess.Popen(
            self.command,
            stdout=slave_fd,
            stderr=slave_fd,
            stdin=subprocess.PIPE,
            close_fds=True
        )

        # Close the slave end in the parent process
        os.close(slave_fd)

    def read_output(self):
        """
        Read and yield output lines from the process in real-time.

        Yields:
            Lines of output from stdout
        """
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")

        buffer = b''

        while True:
            # Check if process has finished
            poll_result = self.process.poll()

            # Use select to check if data is available
            ready, _, _ = select.select([self.master_fd], [], [], 0.1)

            if ready:
                try:
                    chunk = os.read(self.master_fd, 1024)
                    if not chunk:
                        break

                    buffer += chunk

                    # Process complete lines
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        yield line.decode('utf-8', errors='replace')

                except OSError:
                    break

            # If process finished and no more data, break
            if poll_result is not None:
                # Try to read any remaining data
                try:
                    while True:
                        ready, _, _ = select.select([self.master_fd], [], [], 0)
                        if not ready:
                            break
                        chunk = os.read(self.master_fd, 1024)
                        if not chunk:
                            break
                        buffer += chunk
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            yield line.decode('utf-8', errors='replace')
                except OSError:
                    pass

                # Yield any remaining partial line
                if buffer:
                    yield buffer.decode('utf-8', errors='replace')
                break

    def pause(self):
        """Pause the process by sending SIGSTOP."""
        if self.process and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGSTOP)
            print(f"Process {self.process.pid} paused", flush=True)
        else:
            print("Process not running", flush=True)

    def resume(self):
        """Resume the process by sending SIGCONT."""
        if self.process and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGCONT)
            print(f"Process {self.process.pid} resumed", flush=True)
        else:
            print("Process not running", flush=True)

    def terminate(self):
        """Terminate the process gracefully."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass

    def is_running(self):
        """Check if the process is still running."""
        return self.process and self.process.poll() is None

    def get_return_code(self):
        """Get the return code of the process (None if still running)."""
        return self.process.poll() if self.process else None



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
    This function wraps the metal_nws.mm executable and monitor its output.
    """
    executable_path = "./bin/metal_nws"

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

    output_log = deque(maxlen=30)
    runner = MetalNWSRunner(args)
    runner.start()
    seq = 0
    step = 0

    for line in runner.read_output():
        if job.get_state()['status'] == 'cancelled':
            runner.terminate()
            break

        #line = line.strip()
        if line:
            has_progress = False
            if line.startswith("Sequence:"):
                match = re.search(r'Sequence:\s+(\d+)', line)
                if match:
                    seq = int(match.group(1))
                    has_progress=True
            elif line.startswith("Step:"):
                match = re.search(r'Step:\s+(\d+)', line)
                if match:
                    step = int(match.group(1))
                    has_progress=True
            output_log.append(line)
            job.update(output_log=list(output_log))
            if has_progress :
                job.update(progress=f"Seq: {seq} Step: {step}")

    print(f"Process finished with return code: {runner.get_return_code()}")


    #if return_code != 0:
    #    logger.error(f"NWS search job {job.job_id} failed with return code {return_code}")
    #    job.update(status="failed", errors=[f"Process exited with code {return_code}"])
