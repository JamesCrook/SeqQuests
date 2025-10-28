
let pollInterval = 1000;
let pollTimer = null;

function getJobIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('job_id');
}

async function pollJobStatus(updateFunction) {
    if (pollTimer) clearTimeout(pollTimer);
    const jobId = getJobIdFromUrl();
    if (!jobId) return;

    try {
        const data = await parent.apiCall(`/api/job/${jobId}/status`);
        updateFunction(data);
        if (['running', 'initializing'].includes(data.status)) {
            pollTimer = setTimeout(() => pollJobStatus(updateFunction), pollInterval);
        }
    } catch (e) {
        parent.addLog(`Failed to poll status for job ${jobId}: ${e}`, 'error');
    }
}
