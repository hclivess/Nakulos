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
    setupAlertUpdates();
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
initDashboard();
startDashboardUpdater();

export { updateDashboard };