let currentJobId = null;
let currentJobType = null;
let pollTimer = null;
let pollInterval = 1000;
let log = document.getElementById('log');

// --- Logging ---
function addLog(message, type = '') {
  log = document.getElementById('log');
  if (!log) return;
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
      headers: {
        'Content-Type': 'application/json'
      },
      cache: 'no-cache', // Add this line to prevent caching
    };
    if(body) {
      options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if(!response.ok) {
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
  const configContainer = document.getElementById('config-container');
  if (!configContainer) return;

  Lcars.loadPartial('config-container', './partials/jobs.html', () => {
    document.getElementById('config-modal').style.display = 'block';
  });
}

async function startJob() {
  if(!currentJobId) return;
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
  if(!currentJobId) return;
  try {
    await apiCall(`/api/job/${currentJobId}/pause`, 'POST');
    addLog(`Job ${currentJobId} paused.`);
    await refreshJobs();
  } catch (e) {
    addLog(`Failed to pause job: ${e}`, 'error');
  }
}

async function resumeJob() {
  if(!currentJobId) return;
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
    if(jobId === currentJobId) {
      selectJob(null, null);
    }
    await new Promise(resolve => setTimeout(resolve,
    500)); // Add a small delay
    await refreshJobs();
  } catch (e) {
    addLog(`Failed to remove job: ${e}`, 'error');
  }
}

function configureJob(show = true) {
  if(!currentJobId || !currentJobType) return;
  const configContainer = document.getElementById('config-container');
  if (!configContainer) return;

  if (show) {
      // Load the partial
      Lcars.loadPartial('config-container', `./partials/config_${currentJobType}.html`, () => {
          // After loading, we might need to populate values if the partial has inputs
          // But loadJobConfig is called by the partial's script (if we execute scripts).
          // However, we are passing job_id via URL params in the iframe approach.
          // Now we rely on currentJobId being available in scope.

          // Re-execute scripts logic is handled by Lcars.loadPartial.
          document.getElementById('config-modal').style.display = 'block';
          pollJobStatus();
      });
  } else {
      // Just update visibility if we were just toggling or something, but usually show=true when clicking configure
  }
}

function closeModal() {
  const modal = document.getElementById('config-modal');
  if(modal) modal.style.display = 'none';
  pollJobStatus();
}

// --- UI Updates ---
async function refreshJobs() {
  try {
    const jobs = await apiCall('/api/jobs');
    const jobsDiv = document.getElementById('jobs');
    if (!jobsDiv) return;

    jobsDiv.innerHTML = '';
    Object.entries(jobs).forEach(([jobId, job]) => {
      const div = document.createElement('div');
      div.className = 'job-item' + (jobId === currentJobId ?
        ' active-job' : '');
      div.onclick = () => selectJob(jobId, job.job_type);
      div.style.display = 'flex';
      div.style.justifyContent = 'space-between';
      div.style.alignItems = 'center';

      const jobText = document.createElement('span');
      jobText.innerHTML =
        `${jobId.substring(0, 8)}... - ${job.job_type} (${job.status})`;

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
  const buttons = ['startButton', 'pauseButton', 'configureButton',
    'resumeButton'
  ];
  buttons.forEach(id => {
    const el = document.getElementById(id);
    if(el) el.disabled = !jobId;
  });

  if(jobId) {
    // Load the configuration partial in the background to ensure setStatus is available
    // and correct for the selected job type, restoring the auto-update behavior.
    configureJob(false);
  } else {
    closeModal();
  }

  pollJobStatus();
}

async function pollJobStatus() {
  if(pollTimer) clearTimeout(pollTimer);
  if(!currentJobId) return;

  try {
    refreshJobs();
    const data = await apiCall(`/api/job/${currentJobId}/status`);
    updateDisplay(data);
    if(pollInterval > 0 && ['running', 'initializing'].includes(data
      .status)) {
      pollTimer = setTimeout(pollJobStatus, pollInterval);
    }
  } catch (e) {
    if(e.message.includes('404')) {
      addLog('Job not found, deselecting.', 'error');
      selectJob(null, null);
    } else {
      addLog(`Failed to poll status: ${e}`, 'error');
    }
  }
}

function updateDisplay(data) {
  const configureButton = document.getElementById('configureButton');
  if (configureButton) {
      if(['running', 'completed', 'failed', 'cancelled'].includes(data.status)) {
        configureButton.textContent = 'View';
      } else {
        configureButton.textContent = 'Configure';
      }
  }

  // Update Config Modal Progress if open
  // In the partials, we define window.setStatus.
  if (typeof window.setStatus === 'function') {
      window.setStatus(data);
  }

  // Update Job Details on Main Screen
  // We can clone the content from detailDiv if it exists (which it does if config partial is loaded invisible? No)
  // The original code copied from iframe.
  // Now, we need a way to get the detail HTML without opening the config partial?
  // Or we just format it here. But formatting logic was inside the config htmls.
  // Ideally, the partial logic runs.

  // If the config modal is NOT open, we don't have the detailDiv populated by setStatus.
  // But wait, the user wants the "Job Queue is wired up to load the main container... and this too becomes active".

  // To keep it simple: If the modal is closed, we might miss the detailed updates in #job-details.
  // However, `setStatus` updates `#detailDiv`. If that div is in the DOM (in the modal), it gets updated.
  // The original code copied `iframe.contentWindow.document.getElementById('detailDiv').innerHTML` to `job-details`.

  const configDetailDiv = document.getElementById('detailDiv');
  const mainDetailDiv = document.getElementById('job-details');

  if (configDetailDiv && mainDetailDiv) {
      mainDetailDiv.innerHTML = configDetailDiv.innerHTML;
  } else if (mainDetailDiv) {
      // If we don't have the config loaded, we can't show specific details unless we replicate the logic here.
      // Or we load the config partial invisibly?
      // For now, let's leave it blank if config not loaded, or show basic status.
      // mainDetailDiv.innerHTML = `Status: ${data.status}`;
  }
}

function updatePollInterval() {
  const select = document.getElementById('pollInterval');
  if (!select) return;

  pollInterval = parseInt(select.value);
  const status = document.getElementById('pollStatus');
  if(status) {
      status.textContent = pollInterval === 0 ? 'Polling: Disabled' :
        `Polling: Every ${pollInterval/1000}s`;
  }
  addLog(`Poll interval set to ${pollInterval}ms`);
  pollJobStatus();
}

// --- Initialization ---
// We remove the auto-init on window load because this script might be loaded dynamically.
// Instead we export an init function.

window.initJobManagement = async function() {
  addLog('Job Management Initialized');
  await refreshJobs();
  updatePollInterval();

  const params = new URLSearchParams(window.location.search);
  const jobIdFromUrl = params.get('job_id');

  if(jobIdFromUrl) {
    try {
      const data = await apiCall(`/api/job/${jobIdFromUrl}/status`);
      selectJob(jobIdFromUrl, data.job_type);
      configureJob();
    } catch (e) {
      addLog(`Failed to select job from URL: ${e}`, 'error');
      selectJob(null, null);
    }
  } else {
    selectJob(null, null);
  }
};

// If loaded directly (legacy support or if script tag is just present), we can try to init if elements exist
if (document.getElementById('jobs')) {
    //window.addEventListener('load', window.initJobManagement);
}
