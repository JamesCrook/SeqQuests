function getJobIdFromUrl() {
  const params = new URLSearchParams(window.location.search);
  let id = params.get('job_id');
  // Fallback to global currentJobId if defined (when not in iframe)
  if(!id && typeof currentJobId !== 'undefined') {
    id = currentJobId;
  }
  return id;
}

async function loadJobConfig() {
  const jobId = getJobIdFromUrl();
  if(!jobId) return;

  try {
    // If running in same window, apiCall is available globally.
    // If in iframe (legacy), parent.apiCall.
    // We check availability.
    const apiCallFn = (typeof apiCall === 'function') ? apiCall : (parent &&
      parent.apiCall ? parent.apiCall : null);
    const addLogFn = (typeof addLog === 'function') ? addLog : (parent &&
      parent.addLog ? parent.addLog : console.log);

    if(!apiCallFn) {
      console.error("No apiCall function found.");
      return;
    }

    const data = await apiCallFn(`/api/job/${jobId}/status`);
    if(data.config) {
      for(const key in data.config) {
        if(key === 'organisms' && Array.isArray(data.config[key])) {
          data.config[key].forEach(org => {
            const element = document.getElementById(org);
            if(element && element.type === 'checkbox') {
              element.checked = true;
            }
          });
        } else {
          const element = document.getElementById(key);
          if(element) {
            if(element.type === 'checkbox') {
              element.checked = data.config[key];
            } else {
              element.value = data.config[key];
            }
          }
        }
      }
    }
  } catch (e) {
    const addLogFn = (typeof addLog === 'function') ? addLog : (parent &&
      parent.addLog ? parent.addLog : console.log);
    addLogFn(`Failed to load config for job ${jobId}: ${e}`, 'error');
  }
}
