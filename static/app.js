
let currentJobId = null;
let currentJobType = null;
let pollTimer = null;
let pollInterval = 1000;
const log = document.getElementById('log');

// --- Logging ---
function addLog(message, type = '') {
    const timestamp = new Date().toLocaleTimeString();
    const className = type ? ` class="${type}"` : '';
    log.innerHTML += `<p${className}>[${timestamp}] ${message}</p>`;
    log.scrollTop = log.scrollHeight;
}

// --- API Calls ---
async function apiCall(url, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        return await response.json();
    } catch (e) {
        addLog(`API call failed: ${e}`, 'error');
        throw e;
    }
}

// --- Job Management ---
async function addJob() {
    const jobType = prompt("Enter job type (computation, data_munging, sequence_search):");
    if (jobType) {
        try {
            const data = await apiCall('/api/job', 'POST', { job_type: jobType });
            addLog(`Job ${data.job_id} created of type ${jobType}`, 'success');
            selectJob(data.job_id, jobType);
            refreshJobs();
        } catch (e) {
            addLog(`Failed to create job: ${e}`, 'error');
        }
    }
}

async function startJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/start`, 'POST');
        addLog(`Job ${currentJobId} started.`);
    } catch (e) {
        addLog(`Failed to start job: ${e}`, 'error');
    }
}

async function pauseJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/pause`, 'POST');
        addLog(`Job ${currentJobId} paused.`);
    } catch (e) {
        addLog(`Failed to pause job: ${e}`, 'error');
    }
}

async function resumeJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/resume`, 'POST');
        addLog(`Job ${currentJobId} resumed.`);
    } catch (e) {
        addLog(`Failed to resume job: ${e}`, 'error');
    }
}

async function cancelJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/cancel`, 'POST');
        addLog(`Job ${currentJobId} cancelled.`);
    } catch (e) {
        addLog(`Failed to cancel job: ${e}`, 'error');
    }
}

function configureJob() {
    if (!currentJobId || !currentJobType) return;
    const iframe = document.getElementById('config-iframe');
    iframe.src = `/config/${currentJobType}?job_id=${currentJobId}`;
    document.getElementById('config-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('config-modal').style.display = 'none';
}

// --- UI Updates ---
async function refreshJobs() {
    try {
        const jobs = await apiCall('/api/jobs');
        const jobsDiv = document.getElementById('jobs');
        jobsDiv.innerHTML = '';
        Object.entries(jobs).forEach(([jobId, job]) => {
            const div = document.createElement('div');
            div.className = 'job-item' + (jobId === currentJobId ? ' active-job' : '');
            div.innerHTML = `${jobId.substring(0, 8)}... - ${job.job_type} (${job.status})`;
            div.onclick = () => selectJob(jobId, job.job_type);
            jobsDiv.appendChild(div);
        });
    } catch (e) {
        addLog(`Failed to refresh jobs: ${e}`, 'error');
    }
}

function selectJob(jobId, jobType) {
    currentJobId = jobId;
    currentJobType = jobType;

    document.getElementById('currentJobId').textContent = jobId ? `${jobId.substring(0, 12)}...` : 'None';
    document.getElementById('jobTypeText').textContent = jobType || '-';

    // Enable/disable buttons
    const buttons = ['startButton', 'pauseButton', 'cancelButton', 'configureButton', 'resumeButton'];
    buttons.forEach(id => {
        document.getElementById(id).disabled = !jobId;
    });

    refreshJobs();
    pollJobStatus();
}

async function pollJobStatus() {
    if (pollTimer) clearTimeout(pollTimer);
    if (!currentJobId) return;

    try {
        const data = await apiCall(`/api/job/${currentJobId}/status`);
        updateDisplay(data);
        if (pollInterval > 0 && ['running', 'initializing'].includes(data.status)) {
            pollTimer = setTimeout(pollJobStatus, pollInterval);
        }
    } catch (e) {
        if (e.message.includes('404')) {
            addLog('Job not found, deselecting.', 'error');
            selectJob(null, null);
        } else {
            addLog(`Failed to poll status: ${e}`, 'error');
        }
    }
}

function updateDisplay(data) {
    document.getElementById('statusText').textContent = data.status;
    document.getElementById('jobTypeText').textContent = data.job_type;
    document.getElementById('currentStep').textContent = data.current_step || '-';

    const detailsDiv = document.getElementById('job-details');
    detailsDiv.innerHTML = ''; // Clear previous details

    if (data.job_type === 'computation') {
        detailsDiv.innerHTML = `
            <div class="stat">Proteins: <span id="proteins">${data.total_proteins || 0}</span></div>
            <div class="stat">Progress: <span id="pairs">${data.processed_pairs || 0}</span> / <span id="totalPairs">${data.total_pairs || 0}</span> pairs</div>
            <div class="stat">Time: <span id="elapsed">${Math.round(data.elapsed_time || 0)}</span>s</div>
            <div class="stat">Memory: CPU <span id="cpuMem">${Math.round(data.memory_usage_mb || 0)}</span>MB</div>
            <div class="stat">Bridges found: <span id="bridges">${data.bridges_found || 0}</span></div>
        `;
    } else if (data.job_type === 'data_munging') {
        detailsDiv.innerHTML = `
             <div class="stat">Filtered Organisms: <span id="filtered_organisms">${data.filtered_organisms || 0}</span></div>
             <div class="stat">Proteins Processed: <span id="proteins_processed">${data.proteins_processed || 0}</span></div>
        `;
    } else if (data.job_type === 'sequence_search') {
         detailsDiv.innerHTML = `
             <div class="stat">Query Sequence: <span id="query_sequence">${data.query_sequence || ''}</span></div>
             <div class="stat">Matches Found: <span id="matches_found">${data.matches_found || 0}</span></div>
         `;
    }
}

function updatePollInterval() {
    const select = document.getElementById('pollInterval');
    pollInterval = parseInt(select.value);
    document.getElementById('pollStatus').textContent =
        pollInterval === 0 ? 'Polling: Disabled' : `Polling: Every ${pollInterval/1000}s`;
    addLog(`Poll interval set to ${pollInterval}ms`);
    pollJobStatus();
}

// --- Initialization ---
window.addEventListener('load', () => {
    addLog('Page loaded, API ready');
    selectJob(null, null);
    refreshJobs();
    updatePollInterval();
});
