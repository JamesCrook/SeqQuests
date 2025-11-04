
function getJobIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('job_id');
}

async function loadJobConfig() {
    const jobId = getJobIdFromUrl();
    if (!jobId) return;

    try {
        const data = await parent.apiCall(`/api/job/${jobId}/status`);
        if (data.config) {
            for (const key in data.config) {
                if (key === 'organisms' && Array.isArray(data.config[key])) {
                    data.config[key].forEach(org => {
                        const element = document.getElementById(org);
                        if (element && element.type === 'checkbox') {
                            element.checked = true;
                        }
                    });
                } else {
                    const element = document.getElementById(key);
                    if (element) {
                        if (element.type === 'checkbox') {
                            element.checked = data.config[key];
                        } else {
                            element.value = data.config[key];
                        }
                    }
                }
            }
        }
    } catch (e) {
        parent.addLog(`Failed to load config for job ${jobId}: ${e}`, 'error');
    }
}
