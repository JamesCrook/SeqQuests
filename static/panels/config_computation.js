// Config script logic for Computation Job
window.setStatus = function(data) {
  const detailDiv = document.getElementById('detailDiv');
  if(!detailDiv) return;
  detailDiv.innerHTML = `
        <div class="stat">Proteins: <span id="proteins">${data.total_proteins || 0}</span></div>
        <div class="stat">Progress: <span id="pairs">${data.processed_pairs || 0}</span> / <span id="totalPairs">${data.total_pairs || 0}</span> pairs</div>
        <div class="stat">Time: <span id="elapsed">${Math.round(data.elapsed_time || 0)}</span>s</div>
        <div class="stat">Memory: CPU <span id="cpuMem">${Math.round(data.memory_usage_mb || 0)}</span>MB</div>
        <div class="stat">Bridges found: <span id="bridges">${data.bridges_found || 0}</span></div>
    `;
}

window.saveConfigComputation = function() {
  // Assuming global helper to get Job ID (from app.js or job_monitor.js equivalent)
  // Since we are not in an iframe, we use currentJobId from app.js
  // Also need to handle getJobIdFromUrl if not present (e.g. if loaded directly? Unlikely for partials)

  let jobId = null;
  if(typeof currentJobId !== 'undefined') {
    jobId = currentJobId;
  }

  // Fallback if currentJobId is not set but we are in context where we can deduce it?
  // Actually, app.js logic sets currentJobId.

  if(!jobId) {
    addLog('No job selected to configure', 'error');
    return;
  }

  const config = {
    max_proteins: document.getElementById('max_proteins').value,
    use_fast_sw: document.getElementById('use_fast_sw').checked,
  };

  apiCall(`/api/job/${jobId}/configure`, 'POST', {
      config
    })
    .then(() => addLog(`Configuration saved for job ${jobId}`))
    .catch(e => addLog(`Failed to save config: ${e}`, 'error'));
}
