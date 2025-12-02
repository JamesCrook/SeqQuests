"""
Integration example: Using enhanced CommandRunner with Job Manager

This demonstrates how to:
1. Use CommandRunner with filtering in a Job
2. Access buffered output for web interface
3. Provide both standalone and job-managed execution
"""

import threading
import time
from typing import Dict, Any, Optional
from command_runner import CommandRunner, OutputFilter, DisplayMode

class SwSearchJobWithFiltering:
    """
    Example integration of enhanced CommandRunner with a Job.
    Shows how to capture filtered output into job state for web interface.
    """
    
    def __init__(self, job_id: str, manager=None):
        self.job_id = job_id
        self.manager = manager
        self.state = {
            "job_id": job_id,
            "job_type": "sw_search",
            "status": "created",
            "config": {},
            "current_step": "Created",
            "start_time": None,
            "elapsed_time": 0,
            "progress": "No Progress Info",
            "errors": [],
            
            # Buffered outputs by category
            "stats_buffer": [],
            "hits_buffer": [],
            "bench_buffer": [],
            "other_buffer": [],
            
            # Latest line for each category (for quick status)
            "latest_stats": None,
            "latest_hit": None,
            "latest_bench": None,
            
            # Output statistics
            "total_stats_lines": 0,
            "total_hits_lines": 0,
            "total_bench_lines": 0,
        }
        self.lock = threading.Lock()
        self.runner = None

    def update(self, **kwargs):
        """Thread-safe state update"""
        with self.lock:
            self.state.update(kwargs)

    def get_state(self):
        """Thread-safe state retrieval"""
        with self.lock:
            return self.state.copy()

    def configure(self, config: Dict[str, Any]):
        """Configure the job"""
        with self.lock:
            self.state['config'].update(config)

    def start(self):
        """Start the job"""
        if self.state['status'] not in ['created', 'paused']:
            return
        
        self.update(status="running", start_time=time.time())
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        """
        Main job execution - uses CommandRunner with filtering.
        """
        try:
            # Get configuration
            config = self.state['config']
            command = config.get('command', ['echo', 'No command configured'])
            
            # Setup custom filter prefixes if needed
            filter_prefixes = {
                'stats': 'STATS:',
                'hits': 'HIT:',
                'bench': 'BENCH:'
            }
            
            # Buffer sizes - keep more hits, fewer stats
            buffer_sizes = {
                'stats': 10,   # Only keep last 10 stats
                'hits': 100,   # Keep last 100 hits
                'bench': 20    # Keep last 20 benchmarks
            }
            
            # Create runner with custom configuration
            self.runner = CommandRunner(
                command,
                log_error_callback=self._log_error,
                filter_prefixes=filter_prefixes,
                buffer_sizes=buffer_sizes
            )
            
            self.update(current_step="Starting process")
            self.runner.start(cwd=config.get('cwd'))
            
            self.update(current_step="Processing output")
            
            # Process output and update job state
            for category, line in self.runner.read_output_filtered():
                # Update counters
                counter_key = f"total_{category}_lines"
                if counter_key in self.state:
                    with self.lock:
                        self.state[counter_key] += 1
                
                # Update latest for each category
                latest_key = f"latest_{category}"
                if latest_key in self.state:
                    self.update(**{latest_key: line})
                
                # Update progress based on stats lines
                if category == 'stats':
                    self.update(progress=line)
                
                # Check if job should be paused/cancelled
                if self.state['status'] == 'paused':
                    self.runner.pause()
                    while self.state['status'] == 'paused':
                        time.sleep(0.5)
                    self.runner.resume()
                
                if self.state['status'] == 'cancelled':
                    self.runner.terminate()
                    break
            
            # Job completed - sync final buffers to state
            self._sync_buffers_to_state()
            
            if self.state['status'] != 'cancelled':
                self.update(status="completed", current_step="Finished")
                
        except Exception as e:
            self._log_error(f"Job failed: {e}")
            self.update(status="failed", errors=self.state['errors'] + [str(e)])
        finally:
            if self.runner:
                self.runner.terminate()

    def _sync_buffers_to_state(self):
        """Copy buffered output from runner to job state for web access"""
        if not self.runner:
            return
        
        buffers = self.runner.get_buffers()
        with self.lock:
            for category, lines in buffers.items():
                buffer_key = f"{category}_buffer"
                if buffer_key in self.state:
                    self.state[buffer_key] = lines

    def _log_error(self, message: str):
        """Add error to job state"""
        with self.lock:
            self.state['errors'].append(message)

    def get_filtered_output(self, category: str, limit: Optional[int] = None):
        """
        Get filtered output for web interface.
        
        Args:
            category: 'stats', 'hits', 'bench', or 'other'
            limit: Maximum number of lines to return (None for all)
        
        Returns:
            List of lines for the requested category
        """
        buffer_key = f"{category}_buffer"
        with self.lock:
            lines = self.state.get(buffer_key, [])
            if limit:
                return lines[-limit:]
            return lines

    def pause(self):
        """Pause the job and its runner"""
        self.update(status="paused")
        if self.runner:
            self.runner.pause()

    def resume(self):
        """Resume the job and its runner"""
        self.update(status="running")
        if self.runner:
            self.runner.resume()

    def terminate(self):
        """Terminate the job and its runner"""
        self.update(status="cancelled")
        if self.runner:
            self.runner.terminate()


# Example standalone usage
def standalone_example():
    """
    Example of using CommandRunner standalone (not in a job).
    This is what a user would do from command line.
    """
    print("=" * 60)
    print("STANDALONE EXAMPLE")
    print("=" * 60)
    
    # For a real use case, this would be your actual command
    command = ['python3', '/tmp/test_output.py']
    
    # Create runner with custom filtering
    runner = CommandRunner(
        command,
        filter_prefixes={
            'stats': 'STATS:',
            'hits': 'HIT:',
            'bench': 'BENCH:'
        }
    )
    
    # Start the process
    runner.start()
    
    # Option 1: Interactive mode (user can press keys to filter)
    print("\nStarting in INTERACTIVE mode...")
    print("Press 's' for stats, 'h' for hits, 'b' for bench, 'a' for all, '?' for help\n")
    runner.run_interactive()
    
    # Option 2: Non-interactive with fixed filter
    # runner.run_simple(display_mode='hits')
    
    # Wait for completion
    while runner.is_running():
        time.sleep(0.1)
    
    # Show what was captured
    buffers = runner.get_buffers()
    print("\n" + "=" * 60)
    print("CAPTURED OUTPUT SUMMARY")
    print("=" * 60)
    for category, lines in buffers.items():
        print(f"{category.upper()}: {len(lines)} lines")
        if lines:
            print(f"  Latest: {lines[-1][:60]}...")
    
    return runner


# Example job-managed usage
def job_managed_example():
    """
    Example of using CommandRunner within a Job.
    This is for web interface or programmatic control.
    """
    print("\n" + "=" * 60)
    print("JOB-MANAGED EXAMPLE")
    print("=" * 60)
    
    # Create a job
    job = SwSearchJobWithFiltering("test-job-123")
    
    # Configure it
    job.configure({
        'command': ['python3', '/tmp/test_output.py'],
        'cwd': None
    })
    
    # Start it (runs in background thread)
    print("\nStarting job...")
    job.start()
    
    # Monitor progress (simulating what web interface would do)
    last_status = None
    while job.state['status'] == 'running':
        state = job.get_state()
        
        # Show progress updates
        if state['progress'] != last_status:
            print(f"Progress: {state['progress']}")
            last_status = state['progress']
        
        # Show latest hit
        if state['latest_hit']:
            print(f"  {state['latest_hit']}")
        
        time.sleep(1)
    
    # Job finished - show results
    final_state = job.get_state()
    print("\n" + "=" * 60)
    print("JOB COMPLETED")
    print("=" * 60)
    print(f"Status: {final_state['status']}")
    print(f"Total stats: {final_state['total_stats_lines']}")
    print(f"Total hits: {final_state['total_hits_lines']}")
    print(f"Total bench: {final_state['total_bench_lines']}")
    
    # Get specific filtered output (for web interface)
    recent_hits = job.get_filtered_output('hits', limit=5)
    print(f"\nLast 5 hits:")
    for hit in recent_hits:
        print(f"  {hit}")
    
    return job


if __name__ == "__main__":
    import sys
    
    # Create test script first
    from command_runner import create_test_script
    create_test_script()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--job':
        job_managed_example()
    else:
        print("Running standalone example...")
        print("(Use --job flag to see job-managed example)\n")
        standalone_example()