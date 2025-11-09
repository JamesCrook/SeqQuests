
async function processStreamedData() {
    const response = await fetch('http://localhost:8000/stream-data');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    let stats = {
        totalRecords: 0,
        sumCol1: 0,
        sumCol2: 0,
        sumCol3: 0,
        // Add whatever statistics you need
    };
    
    while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
            // Process any remaining data in buffer
            if (buffer.trim()) {
                processLine(buffer, stats);
            }
            break;
        }
        
        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split('\n');
        // Keep the last incomplete line in the buffer
        buffer = lines.pop();
        
        for (const line of lines) {
            if (line.trim()) {
                processLine(line, stats);
            }
        }
        
        // Optional: Update UI periodically
        if (stats.totalRecords % 10000 === 0) {
            updateUI(stats);
        }
    }
    
    return stats;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function processLine(line, stats) {
    if (!line.trim()) {
        return;
    }
    
    const values = line.split(',').map(v => parseInt(v, 10));
    
    // Skip if any value is NaN
    if (values.some(v => isNaN(v))) {
        return;
    }
    
    stats.totalRecords++;
    stats.sumCol1 += values[0];
    stats.sumCol2 += values[1];
    stats.sumCol3 += values[2];
}

function updateUI(stats) {
    console.log(`Processed ${stats.totalRecords} records...`);
    // Update your UI elements
}

// Usage
/*
processStreamedData().then(finalStats => {
    console.log('Final statistics:', finalStats);
    updateUI(finalStats);
});
*/