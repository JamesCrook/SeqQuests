import subprocess
import signal
import os
import time
import pty
import select


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


# Example usage 1: Simple monitoring with real-time output
def example_simple():
    runner = MetalNWSRunner(['./bin/metal_nws', 'query.fasta', 'swissprot.fasta'])
    runner.start()

    for line in runner.read_output():
        print(f"Output: {line}", flush=True)

    print(f"Process finished with return code: {runner.get_return_code()}")


# Example usage 2: Monitoring with pause/resume
def example_pause_resume():
    runner = MetalNWSRunner(['./bin/metal_nws', 'query.fasta', 'swissprot.fasta'])
    runner.start()

    line_count = 0
    for line in runner.read_output():
        print(f"Output: {line}", flush=True)
        line_count += 1

        # Pause after 100 lines
        if line_count == 100:
            print("\n=== Pausing for 5 seconds ===\n", flush=True)
            runner.pause()
            time.sleep(5)
            runner.resume()
            print("\n=== Resumed ===\n", flush=True)

    print(f"Process finished with return code: {runner.get_return_code()}")


# Example usage 3: Monitoring with conditional termination
def example_conditional_stop():
    runner = MetalNWSRunner(['./bin/metal_nws', 'query.fasta', 'swissprot.fasta'])
    runner.start()

    for line in runner.read_output():
        print(f"Output: {line}", flush=True)

        # Stop if we see a certain pattern
        if "ERROR" in line or "FATAL" in line:
            print("Error detected, stopping process", flush=True)
            runner.terminate()
            break

    print(f"Process finished with return code: {runner.get_return_code()}")


# Example usage 4: Real-time monitoring with progress tracking
def example_progress_tracking():
    runner = MetalNWSRunner(['./bin/metal_nws', 'query.fasta', 'swissprot.fasta'])
    runner.start()

    start_time = time.time()
    line_count = 0

    for line in runner.read_output():
        line_count += 1
        elapsed = time.time() - start_time

        # Print progress every 100 lines
        if line_count % 100 == 0:
            print(f"Processed {line_count} lines in {elapsed:.2f}s ({line_count / elapsed:.1f} lines/sec)", flush=True)

        # Print the actual line too
        print(f"  {line}", flush=True)

    total_time = time.time() - start_time
    print(f"\nCompleted: {line_count} lines in {total_time:.2f}s")
    print(f"Average: {line_count / total_time:.1f} lines/sec")


if __name__ == "__main__":
    # Run one of the examples
    example_simple()