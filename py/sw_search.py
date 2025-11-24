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

sw_search is a job for the task runner framework

"""



class SWRunner:
    def __init__(self, 
                 output_dir="sw_results",
                 flush_interval=60):  # Seconds between flushes
        
        # If output_dir is relative, make it relative to PROJECT_ROOT
        # If it's absolute, use it as is.
        self.output_dir = Path(output_dir)
        if not self.output_dir.is_absolute():
             self.output_dir = PROJECT_ROOT / self.output_dir

        self.output_dir.mkdir(exist_ok=True)
        
        self.flush_interval = flush_interval
        
        # File paths
        self.results_file = self.output_dir / "results.csv"
        self.error_log = self.output_dir / "errors.log"
        
        # Runtime state
        self.result_buffer = []
        self.start_seq = self._find_last_sequence()
        self.last_flush_time = time.time()
        self.total_results = 0
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._initialize_results_file()
    
    def _find_last_sequence(self):
        """Find the last query sequence from results file"""
        if not self.results_file.exists():
            return 0
        
        try:
            # Read last line to find highest query_seq
            with open(self.results_file, 'rb') as f:
                # Seek to end and read backwards to find last line
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                
                if file_size == 0:
                    return 0
                
                # Read last ~1KB to find last complete line
                read_size = min(1024, file_size)
                f.seek(-read_size, 2)
                lines = f.read().decode('utf-8', errors='ignore').strip().split('\n')
                
                # Find last line that looks like data (not header)
                for line in reversed(lines):
                    if line and not line.startswith('query_seq'):
                        parts = line.split(',')
                        # We will redo the current query sequence in case the
                        # batch was not complete. Later we will sort -u the results.
                        if len(parts) >= 3:
                            return int(parts[0])
            
        except Exception as e:
            print(f"Warning: Could not read last sequence from {self.results_file}: {e}")
            print("Starting from sequence 0")
        
        return 0
    
    def _initialize_results_file(self):
        """Create CSV header if file doesn't exist"""
        if not self.results_file.exists():
            with open(self.results_file, 'w') as f:
                f.write("query_seq,target_seq,score\n")
    
    def _flush_buffer(self, force=False):
        """Write buffered results to disk if enough time has passed or forced"""
        current_time = time.time()
        elapsed = current_time - self.last_flush_time
        
        if not force and elapsed < self.flush_interval:
            return
        
        if not self.result_buffer:
            return
        
        with open(self.results_file, 'a') as f:
            f.writelines(self.result_buffer)
        
        self.total_results += len(self.result_buffer)
        print(f"[Flushed {len(self.result_buffer)} results, total: {self.total_results}, elapsed: {elapsed:.1f}s]")
        self.result_buffer.clear()
        self.last_flush_time = current_time
    
    def _parse_result_line(self, line):
        """Parse HIT line from Metal output
        Format: HIT:query_seq,target_seq,score
        Example: HIT:0,410645,118
        """
        if not line.startswith("HIT:"):
            return None
        
        try:
            parts = line.split(':')
            
            if len(parts) != 2:
                return None
            
            # CSV format: query_seq,target_seq,score,first,len
            csv_line = f"{parts[1]}\n"
            return csv_line
            
        except (ValueError, IndexError) as e:
            self._log_error(f"Failed to parse line: {line}\nError: {e}")
            return None
    
    def _log_error(self, message):
        """Append error to error log"""
        print(f"{datetime.now().isoformat()} - {message}\n")
        #with open(self.error_log, 'a') as f:
        #    f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def run_all_continuous(self, start_seq=None, num_sequences=570000):
        """Run all queries continuously, flushing periodically"""
        if start_seq is None:
            start_seq = self.start_seq
        
        print(f"\n{'='*70}")
        print(f"SW Runner Starting")
        print(f"Starting from sequence: {start_seq}")
        print(f"Total sequences: {num_sequences}")
        print(f"Flush interval: {self.flush_interval}s")
        print(f"Results directory: {self.output_dir.absolute()}")
        print(f"{'='*70}\n")
        
        # Build command for continuous run
        executable_path = PROJECT_ROOT / "bin/metal_sw"

        cmd = [
            str(executable_path),
            "--start_at", str(start_seq),
            "--num_seqs", str(num_sequences - start_seq),
            "--reporting_threshold", "110"
        ]
        
        overall_start = time.time()
        result_count = 0
        
        try:
            # Run Metal program, capture output line by line

            runner = CommandRunner(cmd, log_error_callback=self._log_error)
            runner.start()

            for line in runner.read_output():            
            
                # Print diagnostic lines for monitoring
                #if not line.startswith("HIT:"):
                print(line)
                
                # Parse and buffer HIT lines
                csv_line = self._parse_result_line(line)
                if csv_line:
                    self.result_buffer.append(csv_line)
                    result_count += 1
                    
                    # Check if it's time to flush (time-based)
                    self._flush_buffer(force=False)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user!")
            process.terminate()
            process.wait()
            self._shutdown()
            return False
            
        except Exception as e:
            self._log_error(f"Exception during run: {e}")
            return False
        
        # Final flush
        self._flush_buffer(force=True)
        
        elapsed = time.time() - overall_start
        
        print(f"\n{'='*70}")
        print(f"ALL QUERIES COMPLETE!")
        print(f"Total results: {self.total_results}")
        print(f"Total time: {elapsed/3600:.2f} hours")
        print(f"{'='*70}\n")
        
        return True
    
    def _shutdown(self):
        """Graceful shutdown - flush buffers"""
        print("\nShutting down gracefully...")
        if self.result_buffer:
            self._flush_buffer(force=True)
            print(f"Flushed {len(self.result_buffer)} remaining results")
        print("Shutdown complete. Restart will resume from last written result.")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self._shutdown()
        sys.exit(0)


def batch_logged():
    import argparse
    
    parser = argparse.ArgumentParser(description="SW Runner - Long-running protein search harness")
    parser.add_argument("--output_dir", default="sw_results", help="Output directory")
    parser.add_argument("--flush_interval", type=int, default=60, help="Seconds between disk flushes")
    parser.add_argument("--num_sequences", type=int, default=570000, help="Total sequences in database")
    parser.add_argument("--start_at", type=int, help="Override starting sequence (default: auto-detect from last line)")
    
    args = parser.parse_args()
    
    runner = SWRunner(
        output_dir=args.output_dir,
        flush_interval=args.flush_interval
    )
    
    start = args.start_at if args.start_at is not None else runner.start_seq
    
    if start > 0:
        print(f"Resuming from sequence {start}")
    else:
        print("Starting fresh from sequence 0")
    
    runner.run_all_continuous(start_seq=start, num_sequences=args.num_sequences)


logger = logging.getLogger(__name__)

class CommandRunner:
    def __init__(self, command, log_error_callback=None):
        """
        Initialize the runner with the command to execute.

        Args:
            command: List of command arguments, e.g., ['./bin/metal_sw', 'query.fasta', 'database.fasta']
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
        """Start the metal_sw process using a pseudo-terminal for unbuffered output."""
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


def run_sw_search(
    job,
    debug_slot: int = -10,
    reporting_threshold: int = 110,
    start_at: int = 0,
    num_seqs: int = 1,
    slow_output: bool = False,
    pam_data: str = "./c_src/pam250.bin",
    fasta_data: str = "./c_src/fasta.bin",
):
    """
    This function wraps the metal_sw.mm executable and monitor its output.
    """
    executable_path = PROJECT_ROOT / "bin/metal_sw"

    # Resolve data paths relative to project root if they are relative
    pam_path = Path(pam_data)
    if not pam_path.is_absolute():
        pam_path = PROJECT_ROOT / pam_path

    fasta_path = Path(fasta_data)
    if not fasta_path.is_absolute():
        fasta_path = PROJECT_ROOT / fasta_path

    args = [
        str(executable_path),
        "--debug_slot", str(debug_slot),
        "--reporting_threshold", str(reporting_threshold),
        "--start_at", str(start_at),
        "--num_seqs", str(num_seqs),
        "--pam_data", str(pam_path),
        "--fasta_data", str(fasta_path),
    ]
    if slow_output:
        args.append("--slow_output")

    output_log = deque(maxlen=30)
    runner = CommandRunner(args)
    runner.start()
    seq = 0
    step = 0

    for line in runner.read_output():
        if not job :
            print( line )
            continue 

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
    #    logger.error(f"SW search job {job.job_id} failed with return code {return_code}")
    #    job.update(status="failed", errors=[f"Process exited with code {return_code}"])

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    #run_sw_search(None)
    batch_logged()

if __name__ == "__main__":
    main()
