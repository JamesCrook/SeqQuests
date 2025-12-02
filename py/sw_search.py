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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from command_runner import CommandRunner

"""

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
        self.results_file = self.output_dir / "sw_results.csv"
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
        executable_path = PROJECT_ROOT / "bin/sw_search_metal"

        cmd = [
            str(executable_path),
            "--start_at", str(start_seq),
            "--num_seqs", str(num_sequences - start_seq),
            "--reporting_threshold", "110",

            #"--debug_slot", str(debug_slot),
            "--pam_data", str(PROJECT_ROOT / "data/pam250.bin"),
            "--fasta_data", str(PROJECT_ROOT / "data/fasta.bin"),            
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


def batch_logged(args):
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


def main():
    parser = argparse.ArgumentParser(description="SW Runner - Long-running protein search harness")
    parser.add_argument("--output_dir", default="sw_results", help="Output directory")
    parser.add_argument("--flush_interval", type=int, default=60, help="Seconds between disk flushes")
    parser.add_argument("--num_sequences", type=int, default=570000, help="Total sequences in database")
    parser.add_argument("--start_at", type=int, help="Override starting sequence (default: auto-detect from last line)", default=10000)
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    #run_sw_search(None)
    batch_logged(args)

if __name__ == "__main__":
    main()
