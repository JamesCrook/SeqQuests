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
import argparse
from datetime import datetime
from pathlib import Path
import termios
import tty
from typing import Optional, Callable, List, Tuple, Dict

from config import PROJECT_ROOT

"""The runners are concerned with long running commands which we may want to interrupt and resume, and from which we poll state information. To do this generically/reusably, we wrap and filter console output
"""


logger = logging.getLogger(__name__)


""" For the high perfromance code, optional temperature tracking.
Unfortunately thsi just reports 0 degrees C or with other attempts, 'Nominal'
There is no actual temperature monitor.
So if you want temperature monitoring, strap a bluetooth thermometer to the case...
I decided it was not worth the hassle.
Leaving commented out code here to document the exploration...
"""
#import shutil
#TEMP_COMMAND = shutil.which('osx-cpu-temp')
#
#def get_cpu_temp():
#    if TEMP_COMMAND:
#        result = subprocess.run([TEMP_COMMAND], 
#                              capture_output=True, text=True)
#        return float(result.stdout.strip().replace('°C', ''))
#    else:
#        return None  # Temperature monitoring unavailable

class OutputFilter:
    """
    Reusable output filter that categorizes lines and maintains buffers.
    Can be used independently or as part of CommandRunner.
    """
    def __init__(self, prefixes: Dict[str, str], buffer_sizes: Dict[str, int] = None):
        """
        Initialize the output filter.
        
        Args:
            prefixes: Dict mapping category names to their prefixes, e.g., 
                     {'stats': 'STATS:', 'hits': 'HIT:', 'bench': 'BENCH:'}
            buffer_sizes: Dict mapping category names to buffer sizes (default: 30 for all)
        """
        self.prefixes = prefixes
        self.buffers = {}
        self.latest = {}  # Store latest line for each category
        
        # Initialize buffers
        default_size = 10
        for category in prefixes.keys():
            size = buffer_sizes.get(category, default_size) if buffer_sizes else default_size
            self.buffers[category] = deque(maxlen=size)
            self.latest[category] = None
    
    def categorize_line(self, line: str) -> Tuple[str, str]:
        """
        Categorize a line based on its prefix.
        
        Returns:
            Tuple of (category, line) where category is the matched category or 'other'
        """
        for category, prefix in self.prefixes.items():
            if line.startswith(prefix):
                return category, line
        return 'other', line
    
    def add_line(self, line: str) -> Tuple[str, str]:
        """
        Add a line to the appropriate buffer.
        
        Returns:
            Tuple of (category, line)
        """
        category, categorized_line = self.categorize_line(line)
        
        if category in self.buffers:
            self.buffers[category].append(categorized_line)
            self.latest[category] = categorized_line
        
        return category, categorized_line
    
    def get_buffer(self, category: str) -> List[str]:
        """Get all lines in a category's buffer."""
        return list(self.buffers.get(category, []))
    
    def get_latest(self, category: str) -> Optional[str]:
        """Get the most recent line for a category."""
        return self.latest.get(category)


class DisplayMode:
    """
    Manages display filtering modes.
    Reusable component for controlling what gets displayed.
    """
    def __init__(self, categories: List[str], default_mode: str = 'all'):
        """
        Initialize display mode manager.
        
        Args:
            categories: List of valid category names
            default_mode: Initial mode ('all' or a category name)
        """
        self.categories = categories
        self.mode = default_mode
        self.mode_history = []
    
    def set_mode(self, mode: str) -> bool:
        """
        Set the display mode.
        
        Returns:
            True if mode was valid and changed, False otherwise
        """
        if mode == 'all' or mode in self.categories:
            self.mode_history.append(self.mode)
            self.mode = mode
            return True
        return False
    
    def cycle_mode(self) -> str:
        """
        Cycle through available modes.
        
        Returns:
            The new mode
        """
        modes = ['all'] + self.categories
        current_idx = modes.index(self.mode) if self.mode in modes else 0
        next_idx = (current_idx + 1) % len(modes)
        self.mode = modes[next_idx]
        return self.mode
    
    def should_display(self, category: str) -> bool:
        """Check if a category should be displayed in current mode."""
        return self.mode == 'all' or self.mode == category
    
    def get_mode_name(self) -> str:
        """Get human-readable mode name."""
        return self.mode.upper() if self.mode != 'all' else 'ALL'


class TerminalController:
    """
    Handles terminal setup/restore and keypress detection.
    Reusable for any interactive terminal application.
    """
    def __init__(self):
        self.old_settings = None
        self.is_setup = False
    
    def setup(self):
        """Setup terminal for raw input mode."""
        if not sys.stdin.isatty():
            logger.warning("stdin is not a TTY, terminal control disabled")
            return
        
        try:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            self.is_setup = True
            logger.debug("Terminal setup for raw input mode")
        except Exception as e:
            logger.warning(f"Could not setup terminal: {e}")
    
    def restore(self):
        """Restore terminal to original settings."""
        if self.old_settings and self.is_setup:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                self.is_setup = False
                logger.debug("Terminal restored to original settings")
            except Exception as e:
                logger.warning(f"Could not restore terminal: {e}")
    
    def check_keypress(self, timeout: float = 0) -> Optional[str]:
        """
        Check for a keypress without blocking.
        
        Args:
            timeout: How long to wait for input (0 = non-blocking)
        
        Returns:
            The key pressed or None
        """
        if not self.is_setup:
            return None
        
        try:
            if select.select([sys.stdin], [], [], timeout)[0]:
                return sys.stdin.read(1)
        except Exception as e:
            logger.debug(f"Error checking keypress: {e}")
        
        return None


class CommandRunner:
    """
    Enhanced CommandRunner with filtering, display modes, and interactive control.
    """
    def __init__(self, command, log_error_callback: Optional[Callable] = None,
                 filter_prefixes: Optional[Dict[str, str]] = None,
                 buffer_sizes: Optional[Dict[str, int]] = None):
        """
        Initialize the runner with the command to execute.

        Args:
            command: List of command arguments
            log_error_callback: Optional callback function for logging errors
            filter_prefixes: Dict of category->prefix mappings for filtering
            buffer_sizes: Dict of category->size mappings for buffers
        """
        self.command = command
        self.process = None
        self.master_fd = None
        self.log_error_callback = log_error_callback
        
        # Setup filtering and display control
        default_prefixes = {
            'stats': 'STATS:',
            'hits': 'HIT:',
            'bench': 'BENCH:'
        }
        self.filter_prefixes = filter_prefixes or default_prefixes
        self.output_filter = OutputFilter(self.filter_prefixes, buffer_sizes)
        
        # Setup display mode control
        categories = list(self.filter_prefixes.keys())
        self.display_mode = DisplayMode(categories, default_mode='all')
        
        # Terminal controller for interactive mode
        self.terminal = TerminalController()

    def _log_error(self, message):
        """Log error using callback if available, otherwise use logger"""
        if self.log_error_callback:
            self.log_error_callback(message)
        else:
            logger.error(message)

    def start(self, cwd: Optional[str] = None):
        """Start the process using a pseudo-terminal for unbuffered output."""
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

    def read_output_filtered(self):
        """
        Read output and yield categorized lines.
        
        Yields:
            Tuples of (category, line) where category is one of the configured
            categories or 'other'
        """
        for line in self.read_output():
            category, categorized_line = self.output_filter.add_line(line)
            yield category, categorized_line

    def run_interactive(self, help_keys: Optional[Dict[str, str]] = None):
        """
        Run the process with interactive display control.
        Press 's', 'h', 'b' to filter by stats/hits/bench, 'a' for all, 'c' to cycle,
        '?' for help, 'q' to quit.
        
        Args:
            help_keys: Optional dict of additional key->description mappings for help
        """
        # Default key bindings
        default_keys = {
            's': 'Show STATS only',
            'h': 'Show HITS only', 
            'b': 'Show BENCH only',
            'a': 'Show ALL output',
            'c': 'Cycle through modes',
            '?': 'Show this help',
            'q': 'Quit'
        }
        keys_help = help_keys or default_keys
        
        self.terminal.setup()
        
        try:
            print(f"Interactive mode - Press '?' for help")
            print(f"Starting: {' '.join(self.command)}\n")
            
            for category, line in self.read_output_filtered():
                # Check for keypress
                key = self.terminal.check_keypress()
                if key:
                    handled = self._handle_keypress(key, keys_help)
                    if key == 'q' and handled:
                        self.terminate()
                        break
                
                # Display line based on current mode
                if self.display_mode.should_display(category) or category == 'other':
                    print(line, flush=True)
        
        finally:
            self.terminal.restore()

    def _handle_keypress(self, key: str, keys_help: Dict[str, str]) -> bool:
        """
        Handle a keypress in interactive mode.
        
        Returns:
            True if key was handled, False otherwise
        """
        if key == '?':
            print("\n" + "=" * 60)
            print("KEYBOARD SHORTCUTS")
            print("=" * 60)
            for k, desc in keys_help.items():
                print(f"  {k} - {desc}")
            print("=" * 60 + "\n")
            return True
        
        elif key == 'a':
            self.display_mode.set_mode('all')
            print(f"\n[Display mode: {self.display_mode.get_mode_name()}]\n", flush=True)
            return True
        
        elif key == 'c':
            self.display_mode.cycle_mode()
            print(f"\n[Display mode: {self.display_mode.get_mode_name()}]\n", flush=True)
            return True
        
        elif key == 's' and 'stats' in self.display_mode.categories:
            self.display_mode.set_mode('stats')
            print(f"\n[Display mode: {self.display_mode.get_mode_name()}]\n", flush=True)
            return True
        
        elif key == 'h' and 'hits' in self.display_mode.categories:
            self.display_mode.set_mode('hits')
            print(f"\n[Display mode: {self.display_mode.get_mode_name()}]\n", flush=True)
            return True
        
        elif key == 'b' and 'bench' in self.display_mode.categories:
            self.display_mode.set_mode('bench')
            print(f"\n[Display mode: {self.display_mode.get_mode_name()}]\n", flush=True)
            return True
        
        elif key == 'q':
            print("\n[Quitting...]\n", flush=True)
            return True
        
        return False

    def run_simple(self, display_mode: str = 'all'):
        """
        Run the process in non-interactive mode with a fixed display mode.
        
        Args:
            display_mode: Which category to display ('all' or a category name)
        """
        self.display_mode.set_mode(display_mode)
        
        for category, line in self.read_output_filtered():
            if self.display_mode.should_display(category) or category == 'other':
                print(line, flush=True)

    def get_buffers(self) -> Dict[str, List[str]]:
        """
        Get all buffered output by category.
        Useful for web interface or status queries.
        
        Returns:
            Dict mapping category names to lists of buffered lines
        """
        return {cat: self.output_filter.get_buffer(cat) 
                for cat in self.output_filter.buffers.keys()}

    def get_latest_by_category(self) -> Dict[str, Optional[str]]:
        """
        Get the latest line for each category.
        Useful for status displays.
        
        Returns:
            Dict mapping category names to their most recent line (or None)
        """
        return self.output_filter.latest.copy()

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


def create_test_script():
    """Create a simple test script that outputs different types of lines."""
    script = """#!/usr/bin/env python3
import time
import random

print("Starting test output generator...")

for i in range(100):
    # Simulate finding hits
    if i % 5 == 0:
        print(f"HIT: Found match {i//5}: score={random.randint(100, 500)}")
    
    # Simulate stats output
    if i % 10 == 0:
        print(f"STATS: Processed={i}, Rate={random.randint(40, 60)}/sec, Memory={random.randint(100, 200)}MB")
    
    # Simulate benchmark output
    if i % 15 == 0:
        print(f"BENCH: Iteration {i}, Time={random.uniform(0.1, 0.5):.3f}s")
    
    # Some regular output
    if i % 7 == 0:
        print(f"Regular output line {i}")
    
    time.sleep(0.2)

print("Test complete!")
"""
    with open('/tmp/test_output.py', 'w') as f:
        f.write(script)
    os.chmod('/tmp/test_output.py', 0o755)
    return '/tmp/test_output.py'


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description="Enhanced Command Runner with interactive display control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test                          # Run interactive test
  %(prog)s --test --mode stats             # Run test showing only STATS
  %(prog)s --command "ls -la"              # Run ls command interactively
  %(prog)s --command "ls -la" --mode all   # Run ls showing everything
        """
    )
    
    parser.add_argument('--test', action='store_true',
                        help='Run test mode with example output')
    parser.add_argument('--command', type=str,
                        help='Command to run (quote if it has spaces)')
    parser.add_argument('--mode', type=str, default='interactive',
                        choices=['interactive', 'all', 'stats', 'hits', 'bench'],
                        help='Display mode (default: interactive)')
    
    args = parser.parse_args()

    if args.test:
        print("Creating test script...")
        test_script = create_test_script()
        command = [test_script]
        print(f"Test script created: {test_script}\n")
    elif args.command:
        command = args.command.split()
    else:
        parser.print_help()
        exit(0)

    # Create runner
    runner = CommandRunner(command)
    
    try:
        runner.start()
        
        if args.mode == 'interactive':
            runner.run_interactive()
        else:
            runner.run_simple(display_mode=args.mode)
        
        # Wait for completion
        while runner.is_running():
            time.sleep(0.1)
        
        return_code = runner.get_return_code()
        print(f"\nProcess exited with code: {return_code}")
        
        # Show buffer stats
        buffers = runner.get_buffers()
        print("\nBuffer Statistics:")
        for category, lines in buffers.items():
            print(f"  {category}: {len(lines)} lines buffered")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        runner.terminate()
    except Exception as e:
        print(f"Error: {e}")
        runner.terminate()
        raise