import { initChart, updateChart } from './chart.js';
import { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState, updateRecentAlerts, setupAlertUpdates } from './alerts.js';
import { updateDowntimes, addDowntime, deleteDowntime } from './downtimes.js';
import { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility } from './utils.js';

let charts = {};
let realtimeUpdateInterval;

const vibrantColors = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
    '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
    '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
    '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080'
];

function getVibrantColor(index) {
    return vibrantColors[index % vibrantColors.length];
}

function updateUrlWithHost(hostname) {
    const url = new URL(window.location);
    url.searchParams.set('host', hostname);
    window.history.pushState({}, '', url);
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
        updateUrlWithHost(selectedHostname);
        await updateDashboard(selectedHostname);
        updateFormVisibility(selectedHostname);
    });
    selector.appendChild(select);
}

function updateHostInfo(hostname, tags) {
    const hostInfoDiv = document.getElementById('hostInfo');
    if (hostInfoDiv) {
        let content = `<p><strong>Hostname: </strong>${hostname}</p>
                       <div class="d-flex flex-wrap gap-2">`;

        if (tags && typeof tags === 'object' && Object.keys(tags).length > 0) {
            for (const [key, value] of Object.entries(tags)) {
                content += `<span class="badge bg-secondary">${key}: ${value}</span>`;
            }
        } else {
            content += '<span class="badge bg-secondary">No tags</span>';
        }

        content += '</div>';
        hostInfoDiv.innerHTML = content;
    } else {
        console.warn("Element with id 'hostInfo' not found");
    }
}

function setupTimeRangeButtons() {
    const timeRanges = ['realtime', 'hour', 'day', 'week', 'month'];
    timeRanges.forEach(range => {
        const button = document.getElementById(`last${range.charAt(0).toUpperCase() + range.slice(1)}Button`);
        if (button) {
            button.addEventListener('click', () => {
                setTimeRange(range);
                const selectedHostname = document.querySelector('#hostSelector select').value;
                updateDashboard(selectedHostname);
                if (range === 'realtime') {
                    setupRealtimeUpdate();
                } else {
                    clearInterval(realtimeUpdateInterval);
                }
            });
        } else {
            console.warn(`Button for ${range} not found`);
        }
    });
}

function setupRealtimeUpdate() {
    clearInterval(realtimeUpdateInterval);
    realtimeUpdateInterval = setInterval(() => {
        const hostname = document.querySelector('#hostSelector select').value;
        updateDashboard(hostname, true);
    }, 5000);  // Update every 5 seconds
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

async function updateDashboard(hostname, isRealtimeUpdate = false) {
    console.log('Updating dashboard...');
    console.log('Selected hostname:', hostname);

    if (hostname === 'all') {
        document.getElementById('hostInfo').style.display = 'none';
        document.getElementById('chartContainer').innerHTML = '';
        Object.values(charts).forEach(chart => chart.destroy());
        charts = {};
    } else {
        document.getElementById('hostInfo').style.display = 'block';
        const latestMetrics = await fetchLatestMetrics();
        console.log('Latest metrics:', latestMetrics);
        const hostData = latestMetrics[hostname];
        if (hostData) {
            const metricNames = Object.keys(hostData.metrics || {});
            console.log('Metric names:', metricNames);

            updateHostInfo(hostname, hostData.tags || {});

            const startDate = new Date(document.getElementById('startDate').value);
            const endDate = new Date(document.getElementById('endDate').value);

            const datasets = {};
            const fetchPromises = metricNames.map(async (metric, index) => {
                const metricData = await fetchMetricHistory(hostname, metric, startDate.getTime() / 1000, endDate.getTime() / 1000);
                const data = metricData.map(point => ({ x: new Date(point[0] * 1000), y: point[1] }));
                datasets[metric] = {
                    label: metric,
                    data: data,
                    borderColor: getVibrantColor(index),
                    fill: false
                };
            });

            await Promise.all(fetchPromises);

            document.getElementById('chartContainer').innerHTML = '';
            for (const metric of metricNames) {
                const chartDiv = document.createElement('div');
                chartDiv.className = 'col-12';
                chartDiv.style.height = '400px';
                chartDiv.innerHTML = `<canvas id="${metric}Chart"></canvas>`;
                document.getElementById('chartContainer').appendChild(chartDiv);
            }

            for (const metric of metricNames) {
                if (charts[metric]) {
                    charts[metric].destroy();
                }
                const ctx = document.getElementById(`${metric}Chart`).getContext('2d');
                charts[metric] = new Chart(ctx, {
                    type: 'line',
                    data: { datasets: [datasets[metric]] },
                    options: {
                        scales: {
                            x: {
                                type: 'time',
                                time: { unit: 'minute' },
                                title: { display: true, text: 'Time' },
                                ticks: { autoSkip: true, maxTicksLimit: 20 },
                                min: startDate,
                                max: endDate
                            },
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'Value' },
                                ticks: { autoSkip: true, maxTicksLimit: 10 }
                            }
                        },
                        plugins: {
                            title: { display: true, text: `${metric} Over Time` },
                            legend: { position: 'top' }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        } else {
            console.error(`No data found for hostname: ${hostname}`);
            updateHostInfo(hostname, {});
            document.getElementById('chartContainer').innerHTML = '';
            Object.values(charts).forEach(chart => chart.destroy());
            charts = {};
        }
    }

    if (!isRealtimeUpdate) {
        await updateRecentAlerts(hostname);
        await updateDowntimes(hostname);
        await updateAlertConfigs(hostname);
    }
}

function checkUrlForHost() {
    const urlParams = new URLSearchParams(window.location.search);
    const hostParam = urlParams.get('host');
    if (hostParam) {
        const hostSelect = document.getElementById('hostSelect');
        if (hostSelect) {
            hostSelect.value = hostParam;
            updateDashboard(hostParam).then(() => {
                updateFormVisibility(hostParam);
            });
        }
    }
}

function initDashboard() {
    fetchHosts().then(hosts => {
        createHostSelector(hosts);
        setupTimeRangeButtons();
        setTimeRange('hour');
        checkUrlForHost();
        updateFormVisibility('all');
        setupAlertUpdates();
        document.getElementById('removeHostButton').addEventListener('click', removeSelectedHost);
        document.getElementById('updateButton').addEventListener('click', handleUpdate);
    });
}

function startDashboardUpdater() {
    setInterval(() => {
        const hostname = document.querySelector('#hostSelector select').value;
        if (!document.getElementById('lastRealtimeButton').classList.contains('active')) {
            updateDashboard(hostname);
        }
    }, 60000);  // Update every minute for non-realtime views
}

async function handleUpdate() {
    console.log('Update button clicked');
    const hostname = document.querySelector('#hostSelector select').value;
    await updateDashboard(hostname);
}

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

document.addEventListener('DOMContentLoaded', function() {
    initDashboard();
    startDashboardUpdater();
});

export { updateDashboard, initDashboard };