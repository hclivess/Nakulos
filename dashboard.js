import { initChart, updateChart } from './chart.js';
import { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState } from './alerts.js';
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
        const metricNames = Object.keys(latestMetrics[hostname].metrics);
        console.log('Metric names:', metricNames);

        updateHostInfo(hostname, latestMetrics[hostname].additional_data);

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
    }

    await updateRecentAlerts(hostname);
    await updateDowntimes(hostname);
    await updateAlertConfigs(hostname);
}

function createHostSelector(hosts) {
    const selector = document.getElementById('hostSelector');
    selector.innerHTML = '<label for="hostSelect" class="form-label">Select Host:</label>';
    const select = document.createElement('select');
    select.id = 'hostSelect';
    select.className = 'form-select';

    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'All Hosts';
    select.appendChild(allOption);

    hosts.forEach(host => {
        const option = document.createElement('option');
        option.value = host.hostname;
        option.textContent = host.additional_data.alias || host.hostname;
        select.appendChild(option);
    });
    select.addEventListener('change', async () => {
        const selectedHostname = select.value;
        await updateDashboard(selectedHostname);
        updateFormVisibility(selectedHostname);
    });
    selector.appendChild(select);
}

function updateHostInfo(hostname, additionalData) {
    const hostInfo = document.getElementById('hostInfo');
    hostInfo.innerHTML = `
        <strong>Hostname:</strong> ${hostname}<br>
        <strong>Alias:</strong> ${additionalData.alias || 'N/A'}<br>
        <strong>Location:</strong> ${additionalData.location || 'N/A'}
    `;
}

async function updateRecentAlerts(hostname) {
    try {
        const response = await fetch(`/fetch/recent_alerts?hostname=${hostname}`);
        const alerts = await response.json();
        const alertsList = document.getElementById('recentAlertsList');
        alertsList.innerHTML = '';
        if (alerts.length === 0) {
            alertsList.innerHTML = '<div class="alert alert-info">No recent alerts.</div>';
        } else {
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-warning';
                alertDiv.innerHTML = `
                    <strong>${hostname === 'all' ? alert.hostname + ' - ' : ''}${alert.alert_metric}</strong>:
                    Value ${alert.alert_value} ${alert.alert_condition} ${alert.alert_threshold}
                    at ${new Date(alert.timestamp * 1000).toLocaleString()}
                `;
                alertsList.appendChild(alertDiv);
            });
        }
    } catch (error) {
        console.error('Error updating recent alerts:', error);
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

async function initDashboard() {
    const hosts = await fetchHosts();
    createHostSelector(hosts);
    setupTimeRangeButtons();
    setTimeRange('hour');
    await updateDashboard('all');
    updateFormVisibility('all');
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
    const hostname = document.querySelector('#hostSelector select').value;
    await addAlertConfig(event, hostname);
    await updateAlertConfigs(hostname);
});

document.getElementById('downtimeForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const hostname = document.querySelector('#hostSelector select').value;
    await addDowntime(event, hostname);
    await updateDowntimes(hostname);
});

// Initialize the dashboard
initDashboard();
startDashboardUpdater();

export { updateDashboard };