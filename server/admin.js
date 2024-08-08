// Function to fetch client IDs and populate the dropdown
async function fetchClientIds() {
    try {
        const response = await fetch('/fetch_client_ids');
        if (response.ok) {
            const clientIds = await response.json();
            const clientIdSelect = document.getElementById('clientId');
            clientIds.forEach(clientId => {
                const option = document.createElement('option');
                option.value = clientId;
                option.textContent = clientId;
                clientIdSelect.appendChild(option);
            });
        } else {
            console.error('Failed to fetch client IDs');
        }
    } catch (error) {
        console.error('Error fetching client IDs:', error);
    }
}

// Call the fetchClientIds function when the page loads
document.addEventListener('DOMContentLoaded', fetchClientIds);

// Function to fetch metrics for a selected host
async function fetchMetricsForHost(hostname) {
    try {
        const response = await fetch(`/fetch/metrics_for_host?hostname=${hostname}`);
        if (response.ok) {
            const metrics = await response.json();
            const metricSelect = document.getElementById('deleteMetricName');
            metricSelect.innerHTML = '<option value="all">All Metrics</option>';
            metrics.forEach(metric => {
                const option = document.createElement('option');
                option.value = metric;
                option.textContent = metric;
                metricSelect.appendChild(option);
            });
        } else {
            console.error('Failed to fetch metrics for host');
        }
    } catch (error) {
        console.error('Error fetching metrics for host:', error);
    }
}

// Event listener for updating client configuration
document.getElementById('updateClientForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const clientId = document.getElementById('clientId').value;
    const hostname = document.getElementById('hostname').value;
    const configJson = document.getElementById('configJson').value;

    try {
        const config = JSON.parse(configJson);
        const response = await fetch('/admin/update_client', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ client_id: clientId, hostname: hostname, config: config }),
        });

        if (response.ok) {
            alert('Client configuration updated successfully');
        } else {
            const errorData = await response.json();
            alert(`Failed to update client configuration: ${errorData.error}`);
        }
    } catch (error) {
        console.error('Error updating client configuration:', error);
        alert('An error occurred while updating client configuration');
    }
});


// Event listener for uploading new metric
document.getElementById('uploadMetricForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const metricName = document.getElementById('metricName').value;
    const metricCode = document.getElementById('metricCode').value;
    const targetTags = document.getElementById('targetTags').value;

    try {
        const response = await fetch('/admin/upload_metric', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: metricName,
                code: metricCode,
                tags: targetTags ? JSON.parse(targetTags) : {}
            }),
        });

        if (response.ok) {
            alert('Metric uploaded successfully');
        } else {
            const errorData = await response.json();
            alert(`Failed to upload metric: ${errorData.error}`);
        }
    } catch (error) {
        console.error('Error uploading metric:', error);
        alert('An error occurred while uploading the metric');
    }
});

// Event listener for updating host tags
document.getElementById('updateTagsForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const hostname = document.getElementById('tagHostname').value;
    const newTags = JSON.parse(document.getElementById('newTags').value);

    try {
        const response = await fetch('/update_tags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ hostname, tags: newTags }),
        });

        if (response.ok) {
            alert('Tags updated successfully');
        } else {
            const errorData = await response.json();
            alert(`Failed to update tags: ${errorData.error}`);
        }
    } catch (error) {
        console.error('Error updating tags:', error);
        alert('An error occurred while updating tags');
    }
});

// Event listener for removing a host
document.getElementById('removeHostForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const hostname = document.getElementById('removeHostname').value;

    if (confirm(`Are you sure you want to remove the host "${hostname}"? This action cannot be undone.`)) {
        try {
            const response = await fetch('/remove_host', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ hostname }),
            });

            if (response.ok) {
                alert(`Host "${hostname}" has been removed successfully.`);
                // Optionally, refresh the page or update the host list
                location.reload();
            } else {
                const errorData = await response.json();
                alert(`Failed to remove host: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error removing host:', error);
            alert('An error occurred while trying to remove the host. Please try again.');
        }
    }
});

// Event listener to update metrics when a host is selected for deletion
document.getElementById('deleteHostname').addEventListener('change', (event) => {
    fetchMetricsForHost(event.target.value);
});

// Event listener for deleting metrics
document.getElementById('deleteMetricsForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const hostname = document.getElementById('deleteHostname').value;
    const metricName = document.getElementById('deleteMetricName').value;
    const startTime = document.getElementById('deleteStartTime').value;
    const endTime = document.getElementById('deleteEndTime').value;

    const confirmMessage = metricName === 'all'
        ? `Are you sure you want to delete all metrics for ${hostname}?`
        : `Are you sure you want to delete the "${metricName}" metric for ${hostname}?`;

    if (confirm(confirmMessage)) {
        try {
            const response = await fetch('/delete_metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    hostname: hostname,
                    metric_name: metricName,
                    start_time: startTime ? new Date(startTime).getTime() / 1000 : null,
                    end_time: endTime ? new Date(endTime).getTime() / 1000 : null
                }),
            });

            if (response.ok) {
                const result = await response.json();
                alert(result.message);
            } else {
                const errorData = await response.json();
                alert(`Failed to delete metrics: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error deleting metrics:', error);
            alert('An error occurred while deleting metrics. Please try again.');
        }
    }
});

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Fetch metrics for the initially selected host
    const initialHostname = document.getElementById('deleteHostname').value;
    if (initialHostname) {
        fetchMetricsForHost(initialHostname);
    }
});