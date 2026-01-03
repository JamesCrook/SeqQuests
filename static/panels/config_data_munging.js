window.saveConfigMunging = async function() {
  const jobId = typeof currentJobId !== 'undefined' ? currentJobId : null;
  const organisms = ['human', 'rat', 'ecoli', 'yeast', 'chicken', 'mouse'];
  const selectedOrganisms = organisms.filter(org => document.getElementById(
    org).checked);

  const config = {
    organisms: selectedOrganisms
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
  let acceptedItemsHtml = '';
  if(data.last_ten_accepted && data.last_ten_accepted.length > 0) {
    acceptedItemsHtml = data.last_ten_accepted.map(item => `<li>${item}</li>`)
      .join('');
  }

  detailDiv.innerHTML = `
        <p><strong>Sequences Examined:</strong> <span id="sequences-examined">${data.sequences_examined || 0}</span></p>
        <p><strong>Proteins Processed:</strong> <span id="proteins-processed">${data.proteins_processed || 0}</span></p>
        <p><strong>Most Recent Item:</strong> <span id="most-recent-item">${data.most_recent_item || '-'}</span></p>
        <h3>Last Ten Accepted Items:</h3>
        <ul id="last-ten-accepted">
            ${acceptedItemsHtml}
        </ul>
    `;
}
