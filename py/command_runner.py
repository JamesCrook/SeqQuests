import subprocess
import errno
import logging
from collections import deque
import signal
import os
import time
import pty
import select
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

"""
CommandRunner is a wrapper for a command. It invokes the command capturing the output via a pty
and it reads that output to maintain a status.

"""

logger = logging.getLogger(__name__)

class CommandRunner:
    def __init__(self, command, log_error_callback=None):
        """
        Initialize the runner with the command to execute.

        Args:
            command: List of command arguments, e.g., ['./bin/sw_search_metal', 'query.fasta', 'database.fasta']
            log_error_callback: Optional callback function for logging errors
        """
        self.command = command
        self.process = None
        self.master_fd = None
        self.log_error_callback = log_error_callback

    def _log_error(self, message):
        """Log error using callback if available, otherwise use logger"""
        if self.log_error_callback:
            self.log_error_callback(message)
        else:
            logger.error(message)

    def start(self):
        """Start the sw_search_metal process using a pseudo-terminal for unbuffered output."""
        # Create a pseudo-terminal
        self.master_fd, slave_fd = pty.openpty()

        self.process = subprocess.Popen(
            self.command,
            stdout=slave_fd,
            stderr=slave_fd,
            stdin=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            close_fds=True
        )

        # Close the slave end in the parent process
        os.close(slave_fd)
        
        logger.info(f"Started process {self.process.pid} with command: {' '.join(self.command)}")

    def read_output(self):
        """
        Read and yield output lines from the process in real-time.

        Yields:
            Lines of output from stdout
        """
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")

        buffer = b''
        consecutive_errors = 0
        max_consecutive_errors = 5

        while True:
            # Check if process has finished
            poll_result = self.process.poll()

            # Use select to check if data is available
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
            except (OSError, ValueError) as e:
                self._log_error(f"select() error: {e}")
                break

            if ready:
                try:
                    chunk = os.read(self.master_fd, 1024)
                    if not chunk:
                        logger.info("Received EOF from process")
                        break

                    # Reset error counter on successful read
                    consecutive_errors = 0
                    buffer += chunk

                    # Process complete lines
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        yield line.decode('utf-8', errors='replace')

                except OSError as e:
                    # Handle interrupted system call - this is recoverable
                    if e.errno == errno.EINTR:
                        logger.debug("Read interrupted by signal (EINTR), retrying...")
                        continue
                    
                    # Handle other OS errors
                    consecutive_errors += 1
                    error_msg = f"OSError reading from process (attempt {consecutive_errors}/{max_consecutive_errors}): {e} (errno: {e.errno})"
                    self._log_error(error_msg)
                    
                    if consecutive_errors >= max_consecutive_errors:
                        self._log_error(f"Too many consecutive errors, terminating read loop")
                        break
                    
                    # Brief pause before retry
                    time.sleep(0.1)
                    continue

            # If process finished and no more data, break
            if poll_result is not None:
                logger.info(f"Process finished with return code: {poll_result}")
                
                # Try to read any remaining data
                try:
                    remaining_attempts = 10
                    while remaining_attempts > 0:
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
                        remaining_attempts -= 1
                        
                except OSError as e:
                    if e.errno != errno.EINTR:
                        self._log_error(f"OSError reading final data: {e}")

                # Yield any remaining partial line
                if buffer:
                    final_line = buffer.decode('utf-8', errors='replace')
                    logger.debug(f"Yielding partial final line: {final_line[:100]}")
                    yield final_line
                break

    def pause(self):
        """Pause the process by sending SIGSTOP."""
        if self.process and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGSTOP)
            logger.info(f"Process {self.process.pid} paused")
            print(f"Process {self.process.pid} paused", flush=True)
        else:
            logger.warning("Cannot pause: Process not running")
            print("Process not running", flush=True)

    def resume(self):
        """Resume the process by sending SIGCONT."""
        if self.process and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGCONT)
            logger.info(f"Process {self.process.pid} resumed")
            print(f"Process {self.process.pid} resumed", flush=True)
        else:
            logger.warning("Cannot resume: Process not running")
            print("Process not running", flush=True)

    def terminate(self):
        """Terminate the process gracefully."""
        if self.process:
            logger.info(f"Terminating process {self.process.pid}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                logger.info(f"Process {self.process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {self.process.pid} did not terminate, killing...")
                self.process.kill()
                logger.info(f"Process {self.process.pid} killed")

        if self.master_fd:
            try:
                os.close(self.master_fd)
                logger.debug("Closed master file descriptor")
            except OSError as e:
                logger.warning(f"Error closing master fd: {e}")

    def is_running(self):
        """Check if the process is still running."""
        return self.process and self.process.poll() is None

    def get_return_code(self):
        """Get the return code of the process (None if still running)."""
        return self.process.poll() if self.process else None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Command Runner module")
    parser.add_argument("--test", action="store_true", help="Run test stub")
    args = parser.parse_args()

    if args.test:
        print("Commmand Runner module test stub")
