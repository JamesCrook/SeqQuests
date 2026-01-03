window.saveConfigSearch = async function() {
  const jobId = typeof currentJobId !== 'undefined' ? currentJobId : null;
  const config = {
    debug_slot: parseInt(document.getElementById('debug_slot').value),
    reporting_threshold: parseInt(document.getElementById(
      'reporting_threshold').value),
    start_at: parseInt(document.getElementById('start_at').value),
    num_seqs: parseInt(document.getElementById('num_seqs').value),
    slow_output: document.getElementById('slow_output').checked,
    pam_data: document.getElementById('pam_data').value,
    fasta_data: document.getElementById('fasta_data').value,
  };

  try {
    await apiCall(`/api/job/${jobId}/configure`, 'POST', {
      config
    });
    addLog(`Configuration for job ${jobId} saved.`, 'success');
    closeModal();
  } catch (e) {
    addLog(`Failed to save configuration: ${e}`, 'error');
  }
}

window.setStatus = function(data) {
  const detailDiv = document.getElementById('detailDiv');
  if(!detailDiv) return;
  let outputLogHtml = '';
  if(data.output_log && data.output_log.length > 0) {
    outputLogHtml = data.output_log.map(item => `<li>${item}</li>`).join('');
  }

  detailDiv.innerHTML = `
        <h3>Output Log (last 10 lines):</h3>
        <ul id="output-log" class="log-output">
            ${outputLogHtml}
        </ul>
    `;
}
