import { initChart, updateChart } from './chart.js';
import { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState, updateRecentAlerts, setupAlertUpdates } from './alerts.js';
import { updateDowntimes, addDowntime, deleteDowntime } from './downtimes.js';
import { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility } from './utils.js';

let chart;

async function updateDashboard(hostname) {
    console.log('Updating dashboard...');
    console.log('Selected hostname:', hostname);

    if (hostname === 'all') {
        document.getElementById('hostInfo').style.display = 'none';
        document.querySelector('.chart-container').style.display = 'none';
        if (chart) {
            chart.destroy();
            chart = null;
        }
    } else {
        document.getElementById('hostInfo').style.display = 'block';
        document.querySelector('.chart-container').style.display = 'block';
        const latestMetrics = await fetchLatestMetrics();
        console.log('Latest metrics:', latestMetrics);
        const hostData = latestMetrics[hostname];
        if (hostData) {
            const metricNames = Object.keys(hostData.metrics || {});
            console.log('Metric names:', metricNames);

            updateHostInfo(hostname, hostData.tags || {});

            const startDate = new Date(document.getElementById('startDate').value).getTime() / 1000;
            const endDate = new Date(document.getElementById('endDate').value).getTime() / 1000;
            const datasets = await Promise.all(metricNames.map(async (metricName) => {
                const history = await fetchMetricHistory(hostname, metricName, startDate, endDate);
                return {
                    label: metricName,
                    data: history.map(point => ({ x: new Date(point[0] * 1000), y: point[1] })),
                    fill: false
                };
            }));

            chart = await updateChart(chart, datasets);
        } else {
            console.error(`No data found for hostname: ${hostname}`);
            updateHostInfo(hostname, {});
        }
    }

    await updateRecentAlerts(hostname);
    await updateDowntimes(hostname);
    await updateAlertConfigs(hostname);
}

function createHostSelector(hosts) {
    console.log('Hosts data received:', hosts);

    const selector = document.getElementById('hostSelector');
    selector.innerHTML = '<label for="hostSelect" class="form-label">Select Host:</label>';
    const select = document.createElement('select');
    select.id = 'hostSelect';
    select.className = 'form-select';

    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'All Hosts';
    select.appendChild(allOption);

    if (typeof hosts === 'object' && hosts !== null) {
        Object.entries(hosts).forEach(([hostname, hostData]) => {
            const option = document.createElement('option');
            option.value = hostname;
            option.textContent = hostData.tags && hostData.tags.alias ? hostData.tags.alias : hostname;
            select.appendChild(option);
        });
    } else {
        console.error('Unexpected hosts data format:', hosts);
    }

    select.addEventListener('change', async () => {
        const selectedHostname = select.value;
        await updateDashboard(selectedHostname);
        updateFormVisibility(selectedHostname);
    });
    selector.appendChild(select);
}

function updateHostInfo(hostname, tags) {
    const hostInfoDiv = document.getElementById('hostInfo');
    if (hostInfoDiv) {
        let content = `<p><strong>Hostname: </strong>${hostname}</p>
                       <p><strong>Tags:</strong></p>
                       <ul>`;

        if (tags && typeof tags === 'object') {
            for (const [key, value] of Object.entries(tags)) {
                content += `<li>${key}: ${value}</li>`;
            }
        } else {
            content += '<li>No tags available</li>';
        }

        content += '</ul>';
        hostInfoDiv.innerHTML = content;
    } else {
        console.warn("Element with id 'hostInfo' not found");
    }
}

function setupTimeRangeButtons() {
    const timeRanges = ['hour', 'day', 'week', 'month'];
    timeRanges.forEach(range => {
        document.getElementById(`last${range.charAt(0).toUpperCase() + range.slice(1)}Button`)
            .addEventListener('click', () => {
                setTimeRange(range);
                updateDashboard(document.querySelector('#hostSelector select').value);
            });
    });
}

async function removeSelectedHost() {
    const selectedHostname = document.querySelector('#hostSelector select').value;
    if (selectedHostname === 'all') {
        alert('Please select a specific host to remove.');
        return;
    }

    if (confirm(`Are you sure you want to remove the host "${selectedHostname}"? This action cannot be undone.`)) {
        try {
            const response = await fetch('/remove_host', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ hostname: selectedHostname }),
            });

            if (response.ok) {
                alert(`Host "${selectedHostname}" has been removed successfully.`);
                // Refresh the host list and update the dashboard
                const hosts = await fetchHosts();
                createHostSelector(hosts);
                await updateDashboard('all');
            } else {
                const errorData = await response.json();
                alert(`Failed to remove host: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error removing host:', error);
            alert('An error occurred while trying to remove the host. Please try again.');
        }
    }
}


async function initDashboard() {
    const hosts = await fetchHosts();
    createHostSelector(hosts);
    setupTimeRangeButtons();
    setTimeRange('hour');
    await updateDashboard('all');
    updateFormVisibility('all');
    setupAlertUpdates();
    document.getElementById('removeHostButton').addEventListener('click', removeSelectedHost);
}

function startDashboardUpdater() {
    setInterval(() => {
        const hostname = document.querySelector('#hostSelector select').value;
        updateDashboard(hostname);
    }, 60000);  // Update every minute
}

// Event listeners

document.getElementById('alertForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    await addAlertConfig(event);
    const hostname = document.querySelector('#hostSelector select').value;
    await updateAlertConfigs(hostname);
});

document.getElementById('downtimeForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    await addDowntime(event);
    const hostname = document.querySelector('#hostSelector select').value;
    await updateDowntimes(hostname);
});

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    initDashboard();
    startDashboardUpdater();
});

export { updateDashboard };