from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
from datetime import datetime
import json
from typing import Dict, Any
import threading
import time

# Own modules
from nws import FastNWS

app = FastAPI()

# Serve static files (your HTML/JS client)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global progress state
class ProgressMonitor:
    def __init__(self):
        self.state = {
            "status": "idle",
            "current_step": "",
            "total_proteins": 0,
            "processed_pairs": 0,
            "total_pairs": 0,
            "current_batch": 0,
            "total_batches": 0,
            "start_time": None,
            "elapsed_time": 0,
            "estimated_remaining": 0,
            "score_statistics": {},
            "bridges_found": 0,
            "memory_usage_mb": 0,
            "gpu_memory_mb": 0,
            "errors": []
        }
        self.lock = threading.Lock()
        self.update_callbacks = []
        
    def update(self, **kwargs):
        with self.lock:
            self.state.update(kwargs)
            if self.state["start_time"]:
                self.state["elapsed_time"] = time.time() - self.state["start_time"]
            
            # Calculate estimated time remaining
            if self.state["total_pairs"] > 0 and self.state["processed_pairs"] > 0:
                rate = self.state["processed_pairs"] / self.state["elapsed_time"]
                remaining = self.state["total_pairs"] - self.state["processed_pairs"]
                self.state["estimated_remaining"] = remaining / rate if rate > 0 else 0
        
        # Notify callbacks
        for callback in self.update_callbacks:
            callback(self.state)
    
    def get_state(self):
        with self.lock:
            return self.state.copy()
    
    def add_callback(self, callback):
        self.update_callbacks.append(callback)
    
    def remove_callback(self, callback):
        self.update_callbacks.remove(callback)

# Global instance
progress_monitor = ProgressMonitor()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Send initial state
    await websocket.send_json(progress_monitor.get_state())
    
    # Queue for updates
    update_queue = asyncio.Queue()
    
    def update_callback(state):
        asyncio.create_task(update_queue.put(state))
    
    progress_monitor.add_callback(update_callback)
    
    try:
        # Send updates as they come
        while True:
            state = await update_queue.get()
            await websocket.send_json(state)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        progress_monitor.remove_callback(update_callback)

# REST endpoints
@app.get("/api/progress")
async def get_progress():
    """Get current progress state"""
    return progress_monitor.get_state()

@app.get("/api/statistics")
async def get_statistics():
    """Get detailed statistics"""
    state = progress_monitor.get_state()
    return {
        "score_statistics": state.get("score_statistics", {}),
        "bridges_found": state.get("bridges_found", 0),
        "memory_usage_mb": state.get("memory_usage_mb", 0),
        "gpu_memory_mb": state.get("gpu_memory_mb", 0)
    }

@app.post("/api/cancel")
async def cancel_computation():
    """Cancel ongoing computation"""
    progress_monitor.update(status="cancelling")
    # Set a flag that your computation checks
    return {"status": "cancelling"}

# Modified computation functions with progress tracking
import psutil
import torch

def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process()
    cpu_mb = process.memory_info().rss / 1024 / 1024
    
    gpu_mb = 0
    if torch.cuda.is_available():
        gpu_mb = torch.cuda.memory_allocated() / 1024 / 1024
    
    return cpu_mb, gpu_mb

class FastNWSWithProgress(FastNWS):
    def compute_all_pairs(self, sequences):
        """Compute full NxN score matrix with progress tracking"""
        n = len(sequences)
        total_pairs = n * (n + 1) // 2  # Upper triangular
        
        # Update progress
        progress_monitor.update(
            status="computing",
            current_step="Computing pairwise scores",
            total_proteins=n,
            total_pairs=total_pairs,
            processed_pairs=0,
            start_time=time.time()
        )
        
        # Preallocate score matrix
        scores = np.zeros((n, n), dtype=np.float32)
        
        # Convert sequences to tensors
        progress_monitor.update(current_step="Preprocessing sequences")
        seq_tensors = sequences  # For composition, we keep as strings
        
        # Batch computation
        processed = 0
        total_batches = ((n + self.batch_size - 1) // self.batch_size) ** 2
        current_batch = 0
        
        for i in range(0, n, self.batch_size):
            for j in range(i, n, self.batch_size):
                current_batch += 1
                
                # Check if cancelled
                if progress_monitor.state["status"] == "cancelling":
                    raise InterruptedError("Computation cancelled by user")
                
                batch_i = seq_tensors[i:i+self.batch_size]
                batch_j = seq_tensors[j:j+self.batch_size]
                
                # Compute batch scores
                batch_scores = self.batch_nws(batch_i, batch_j)
                
                # Fill score matrix (symmetric)
                for bi, ii in enumerate(range(i, min(i+self.batch_size, n))):
                    for bj, jj in enumerate(range(j, min(j+self.batch_size, n))):
                        scores[ii, jj] = batch_scores[bi, bj]
                        scores[jj, ii] = batch_scores[bi, bj]
                        if ii <= jj:
                            processed += 1
                
                # Update progress
                cpu_mb, gpu_mb = get_memory_usage()
                progress_monitor.update(
                    processed_pairs=processed,
                    current_batch=current_batch,
                    total_batches=total_batches,
                    memory_usage_mb=cpu_mb,
                    gpu_memory_mb=gpu_mb,
                    score_statistics={
                        "min": float(np.min(scores[scores != 0])) if np.any(scores != 0) else 0,
                        "max": float(np.max(scores)),
                        "mean": float(np.mean(scores[scores != 0])) if np.any(scores != 0) else 0,
                    }
                )
        
        progress_monitor.update(
            status="completed",
            current_step="Score computation complete"
        )
        
        return scores

def detect_bridges_with_progress(score_matrix, proteins, threshold=-20):
    """Find bridges using MST approach with progress tracking"""
    progress_monitor.update(
        status="computing",
        current_step="Detecting bridges",
        bridges_found=0
    )
    
    # Your existing bridge detection code here
    # Add progress updates as appropriate
    
    # Simulate for now
    import time
    time.sleep(2)
    bridges = []  # Your actual bridge detection
    
    progress_monitor.update(
        bridges_found=len(bridges),
        current_step="Bridge detection complete"
    )
    
    return bridges

# Main computation endpoint
@app.post("/api/start_computation")
async def start_computation(config: Dict[str, Any]):
    """Start the computation in background"""
    
    def run_analysis():
        try:
            # Select proteins
            progress_monitor.update(
                status="computing",
                current_step="Selecting proteins"
            )
            proteins_df = select_diverse_proteins(config.get("n_proteins", 1000))
            sequences = proteins_df['sequence'].tolist()
            protein_ids = proteins_df['id'].tolist()
            
            # Compute scores
            nws = FastNWSWithProgress(batch_size=config.get("batch_size", 100))
            score_matrix = nws.compute_all_pairs(sequences)
            
            # Store compressed
            progress_monitor.update(current_step="Compressing and storing results")
            handler = ScoreMatrixHandler()
            handler.compress_and_store(score_matrix, protein_ids)
            
            # Find bridges
            bridges = detect_bridges_with_progress(
                score_matrix, 
                protein_ids, 
                threshold=config.get("threshold", -20)
            )
            
            progress_monitor.update(
                status="completed",
                current_step="Analysis complete"
            )
            
        except InterruptedError:
            progress_monitor.update(
                status="cancelled",
                current_step="Computation cancelled"
            )
        except Exception as e:
            progress_monitor.update(
                status="error",
                current_step=f"Error: {str(e)}",
                errors=progress_monitor.state["errors"] + [str(e)]
            )
    
    # Start in background thread
    threading.Thread(target=run_analysis, daemon=True).start()
    
    return {"status": "started"}

# Serve the main page
@app.get("/")
async def read_root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protein Analysis Monitor</title>
        <script src="/static/monitor.js"></script>
        <link rel="stylesheet" href="/static/monitor.css">
    </head>
    <body>
        <div id="app">
            <h1>Protein Similarity Analysis</h1>
            <div id="progress-container"></div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)