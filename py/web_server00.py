from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime
import json
import threading
import time
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def get_state(self):
        with self.lock:
            return self.state.copy()
    
    def add_callback(self, callback):
        self.update_callbacks.append(callback)
    
    def remove_callback(self, callback):
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

# Global instance
progress_monitor = ProgressMonitor()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt")
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    # Send initial state
    try:
        await websocket.send_json(progress_monitor.get_state())
    except Exception as e:
        logger.error(f"Error sending initial state: {e}")
        return
    
    # Queue for updates
    update_queue = asyncio.Queue()
    
    async def update_callback(state):
        await update_queue.put(state)
    
    # Wrapper to handle sync/async callback
    def sync_callback(state):
        asyncio.create_task(update_callback(state))
    
    progress_monitor.add_callback(sync_callback)
    
    try:
        # Send updates as they come
        while True:
            state = await update_queue.get()
            await websocket.send_json(state)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        progress_monitor.remove_callback(sync_callback)

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
    return {"status": "cancelling"}

# Demo computation endpoint
@app.post("/api/start_computation")
async def start_computation(config: Dict[str, Any] = None):
    """Start a demo computation in background"""
    
    def demo_computation():
        try:
            n_proteins = config.get("n_proteins", 1000) if config else 1000
            total_pairs = n_proteins * (n_proteins + 1) // 2
            
            progress_monitor.update(
                status="computing",
                current_step="Initializing",
                total_proteins=n_proteins,
                total_pairs=total_pairs,
                processed_pairs=0,
                start_time=time.time()
            )
            
            # Simulate computation
            for i in range(100):
                # Check if cancelled
                if progress_monitor.state["status"] == "cancelling":
                    progress_monitor.update(
                        status="cancelled",
                        current_step="Computation cancelled"
                    )
                    return
                
                # Simulate progress
                processed = int((i + 1) / 100 * total_pairs)
                progress_monitor.update(
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
            
            progress_monitor.update(
                status="completed",
                current_step="Analysis complete"
            )
            
        except Exception as e:
            logger.error(f"Error in computation: {e}")
            progress_monitor.update(
                status="error",
                current_step=f"Error: {str(e)}",
                errors=progress_monitor.state["errors"] + [str(e)]
            )
    
    # Start in background thread
    threading.Thread(target=demo_computation, daemon=True).start()
    
    return {"status": "started"}

# Serve a simple test page
@app.get("/")
async def read_root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Protein Analysis Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #status { font-weight: bold; }
            #progress { margin: 20px 0; }
            button { margin: 5px; padding: 10px; }
            .stat { margin: 5px 0; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>Protein Similarity Analysis Monitor</h1>
        
        <div>
            <button onclick="startComputation()">Start Computation</button>
            <button onclick="cancelComputation()">Cancel</button>
            <button onclick="getProgress()">Get Progress (REST)</button>
            <button onclick="testConnection()">Test WebSocket</button>
        </div>
        
        <div id="status">Status: <span id="statusText">idle</span></div>
        <div id="currentStep">Step: <span id="stepText">-</span></div>
        <div id="wsStatus">WebSocket: <span id="wsStatusText">disconnected</span></div>
        
        <div id="progress">
            <div class="stat">Proteins: <span id="proteins">0</span></div>
            <div class="stat">Progress: <span id="pairs">0</span> / <span id="totalPairs">0</span> pairs</div>
            <div class="stat">Time: <span id="elapsed">0</span>s (remaining: <span id="remaining">0</span>s)</div>
            <div class="stat">Memory: CPU <span id="cpuMem">0</span>MB, GPU <span id="gpuMem">0</span>MB</div>
            <div class="stat">Bridges found: <span id="bridges">0</span></div>
        </div>
        
        <div id="log" style="margin-top: 20px; padding: 10px; background: #f0f0f0; height: 200px; overflow-y: auto;">
            <h3>Log</h3>
        </div>
        
        <script>
            let ws = null;
            const log = document.getElementById('log');
            
            function addLog(message, type = '') {
                const timestamp = new Date().toLocaleTimeString();
                const className = type ? ` class="${type}"` : '';
                log.innerHTML += `<p${className}>[${timestamp}] ${message}</p>`;
                log.scrollTop = log.scrollHeight;
            }
            
            function updateWSStatus(status) {
                document.getElementById('wsStatusText').textContent = status;
            }
            
            function connectWebSocket() {
                // Get the current page's host and protocol
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/progress`;
                
                addLog(`Connecting to ${wsUrl}...`);
                updateWSStatus('connecting');
                
                try {
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = () => {
                        addLog('WebSocket connected', 'success');
                        updateWSStatus('connected');
                    };
                    
                    ws.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            updateDisplay(data);
                            addLog(`Update received: ${data.status} - ${data.current_step}`);
                        } catch (e) {
                            addLog(`Error parsing message: ${e}`, 'error');
                        }
                    };
                    
                    ws.onerror = (error) => {
                        addLog('WebSocket error occurred', 'error');
                        updateWSStatus('error');
                    };
                    
                    ws.onclose = (event) => {
                        addLog(`WebSocket disconnected (code: ${event.code})`, 'error');
                        updateWSStatus('disconnected');
                        // Reconnect after 3 seconds
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                } catch (e) {
                    addLog(`Failed to create WebSocket: ${e}`, 'error');
                    updateWSStatus('failed');
                }
            }
            
            function updateDisplay(data) {
                document.getElementById('statusText').textContent = data.status;
                document.getElementById('stepText').textContent = data.current_step || '-';
                document.getElementById('proteins').textContent = data.total_proteins;
                document.getElementById('pairs').textContent = data.processed_pairs;
                document.getElementById('totalPairs').textContent = data.total_pairs;
                document.getElementById('elapsed').textContent = Math.round(data.elapsed_time);
                document.getElementById('remaining').textContent = Math.round(data.estimated_remaining);
                document.getElementById('cpuMem').textContent = Math.round(data.memory_usage_mb);
                document.getElementById('gpuMem').textContent = Math.round(data.gpu_memory_mb);
                document.getElementById('bridges').textContent = data.bridges_found;
            }
            
            async function startComputation() {
                try {
                    const response = await fetch('/api/start_computation', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            n_proteins: 1000,
                            batch_size: 100,
                            threshold: -20
                        })
                    });
                    const data = await response.json();
                    addLog(`Computation started: ${JSON.stringify(data)}`, 'success');
                } catch (e) {
                    addLog(`Failed to start computation: ${e}`, 'error');
                }
            }
            
            async function cancelComputation() {
                try {
                    const response = await fetch('/api/cancel', {method: 'POST'});
                    const data = await response.json();
                    addLog(`Cancel requested: ${JSON.stringify(data)}`);
                } catch (e) {
                    addLog(`Failed to cancel: ${e}`, 'error');
                }
            }
            
            async function getProgress() {
                try {
                    const response = await fetch('/api/progress');
                    const data = await response.json();
                    updateDisplay(data);
                    addLog('Progress fetched via REST');
                } catch (e) {
                    addLog(`Failed to get progress: ${e}`, 'error');
                }
            }
            
            function testConnection() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    addLog('WebSocket is connected and ready', 'success');
                } else {
                    addLog('WebSocket is not connected', 'error');
                    connectWebSocket();
                }
            }
            
            // Connect on load
            window.addEventListener('load', () => {
                addLog('Page loaded, initializing WebSocket connection...');
                connectWebSocket();
            });
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")