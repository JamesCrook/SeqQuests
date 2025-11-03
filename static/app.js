
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
            cache: 'no-cache', // Add this line to prevent caching
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
    window.location.href = '/jobs';
}

async function startJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/start`, 'POST');
        addLog(`Job ${currentJobId} started.`);
        pollJobStatus();
        await refreshJobs();
    } catch (e) {
        addLog(`Failed to start job: ${e}`, 'error');
    }
}

async function pauseJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/pause`, 'POST');
        addLog(`Job ${currentJobId} paused.`);
        await refreshJobs();
    } catch (e) {
        addLog(`Failed to pause job: ${e}`, 'error');
    }
}

async function resumeJob() {
    if (!currentJobId) return;
    try {
        await apiCall(`/api/job/${currentJobId}/resume`, 'POST');
        addLog(`Job ${currentJobId} resumed.`);
        await refreshJobs();
    } catch (e) {
        addLog(`Failed to resume job: ${e}`, 'error');
    }
}

async function removeJob(jobId) {
    try {
        await apiCall(`/api/job/${jobId}`, 'DELETE');
        addLog(`Job ${jobId} deleted.`);
        if (jobId === currentJobId) {
            selectJob(null, null);
        }
        await new Promise(resolve => setTimeout(resolve, 500)); // Add a small delay
        await refreshJobs();
    } catch (e) {
        addLog(`Failed to remove job: ${e}`, 'error');
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
            div.onclick = () => selectJob(jobId, job.job_type);
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';

            const jobText = document.createElement('span');
            jobText.innerHTML = `${jobId.substring(0, 8)}... - ${job.job_type} (${job.status})`;

            const statusText = document.createElement('span');
            statusText.innerHTML = job.progress ?? "No Progress Info";

            const trashIcon = document.createElement('span');
            trashIcon.innerHTML = "🗑️"
            trashIcon.onclick = (e) => {
                e.stopPropagation();
                removeJob(jobId);
            };

            div.appendChild(jobText);
            div.appendChild(statusText);
            div.appendChild(trashIcon);
            jobsDiv.appendChild(div);
        });
    } catch (e) {
        addLog(`Failed to refresh jobs: ${e}`, 'error');
    }
}

function selectJob(jobId, jobType) {
    currentJobId = jobId;
    currentJobType = jobType;

    // Enable/disable buttons
    const buttons = ['startButton', 'pauseButton', 'configureButton', 'resumeButton'];
    buttons.forEach(id => {
        document.getElementById(id).disabled = !jobId;
    });

    pollJobStatus();
}

async function pollJobStatus() {
    if (pollTimer) clearTimeout(pollTimer);
    if (!currentJobId) return;

    try {
        refreshJobs();
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
    //document.getElementById('statusText').textContent = data.status;
    //document.getElementById('jobTypeText').textContent = data.job_type;
    //document.getElementById('currentStep').textContent = data.current_step || '-';

    const configureButton = document.getElementById('configureButton');
    if (['running', 'completed', 'failed', 'cancelled'].includes(data.status)) {
        configureButton.textContent = 'View';
    } else {
        configureButton.textContent = 'Configure';
    }

    const detailsDiv = document.getElementById('job-details');
    if( !detailsDiv )
        return;
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
window.addEventListener('load', async () => {
    addLog('Page loaded, API ready');
    await refreshJobs();
    updatePollInterval();

    const params = new URLSearchParams(window.location.search);
    const jobIdFromUrl = params.get('job_id');

    if (jobIdFromUrl) {
        try {
            const data = await apiCall(`/api/job/${jobIdFromUrl}/status`);
            selectJob(jobIdFromUrl, data.job_type);
        } catch (e) {
            addLog(`Failed to select job from URL: ${e}`, 'error');
            selectJob(null, null);
        }
    } else {
        selectJob(null, null);
    }
});
