// static/monitor.js
class ProgressMonitor {
    constructor() {
        this.ws = null;
        this.connectWebSocket();
    }
    
    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/ws/progress');
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateDisplay(data);
        };
    }
    
    updateDisplay(data) {
        // Your display update logic
        console.log('Progress update:', data);
    }
    
    async startComputation() {
        const response = await fetch('/api/start_computation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                n_proteins: 1000,
                batch_size: 100,
                threshold: -20
            })
        });
    }
}