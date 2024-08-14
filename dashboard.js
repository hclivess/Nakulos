import { initChart, updateChart, addDataToChart, updateChartTimeRange } from './chart.js';
import { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState, updateRecentAlerts, setupAlertUpdates } from './alerts.js';
import { updateDowntimes, addDowntime, deleteDowntime } from './downtimes.js';
import { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility, createHostSelector, updateHostInfo, getVibrantColor, processMetricData, displayMessages } from './utils.js';

let charts = {};
let realtimeUpdateInterval;

async function updateDashboard(hostname, isRealtimeUpdate = false) {
    console.log('Updating dashboard...');
    console.log('Selected hostname:', hostname);

    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    let startDate = new Date(startDateInput.value);
    let endDate = new Date(endDateInput.value);

    console.log('Start date:', startDate);
    console.log('End date:', endDate);

    const activeTimeRangeButton = document.querySelector('.dropdown-item.active');
    const isCustomRange = !activeTimeRangeButton;

    if (isRealtimeUpdate && !isCustomRange) {
        endDate = new Date();
        const timeDiff = endDate - startDate;
        startDate = new Date(endDate - timeDiff);

        startDateInput.value = startDate.toISOString().slice(0, 16);
        endDateInput.value = endDate.toISOString().slice(0, 16);
        console.log('Updated start date:', startDate);
        console.log('Updated end date:', endDate);
    }

    if (hostname === 'all') {
        document.getElementById('hostInfo').style.display = 'none';
        document.getElementById('chartContainer').innerHTML = '';
        Object.values(charts).forEach(chart => chart.destroy());
        charts = {};
    } else {
        document.getElementById('hostInfo').style.display = 'block';
        try {
            const latestMetrics = await fetchLatestMetrics();
            console.log('Latest metrics:', latestMetrics);
            const hostData = latestMetrics[hostname];
            if (hostData) {
                const metricNames = Object.keys(hostData.metrics || {});
                console.log('Metric names:', metricNames);

                updateHostInfo(hostname, hostData.tags || {});

                const datasets = {};
                const messages = [];
                const fetchPromises = metricNames.map(async (metricName) => {
                    try {
                        console.log(`Fetching history for ${hostname} - ${metricName}`);
                        const metricData = await fetchMetricHistory(hostname, metricName, startDate.getTime() / 1000, endDate.getTime() / 1000);
                        console.log(`Fetched data for ${metricName}:`, metricData);
                        datasets[metricName] = processMetricData(metricData, metricName);
                        console.log(`Processed datasets for ${metricName}:`, datasets[metricName]);

                        // Collect messages
                        metricData.forEach(point => {
                            Object.entries(point).forEach(([subMetricName, subMetricData]) => {
                                if (subMetricData && typeof subMetricData === 'object' && 'message' in subMetricData) {
                                    console.log(`Found message for ${metricName}.${subMetricName}:`, subMetricData.message);
                                    messages.push({
                                        timestamp: new Date(point.timestamp * 1000),
                                        metricName: `${metricName}.${subMetricName}`,
                                        message: subMetricData.message
                                    });
                                }
                            });
                        });
                    } catch (error) {
                        console.error(`Error processing data for ${metricName}:`, error);
                    }
                });

                await Promise.all(fetchPromises);

                console.log('All collected messages:', messages);

                document.getElementById('chartContainer').innerHTML = '';
                for (const metricName of metricNames) {
                    const chartDiv = document.createElement('div');
                    chartDiv.className = 'col-12';
                    chartDiv.style.height = '400px';
                    chartDiv.innerHTML = `<canvas id="${metricName}Chart"></canvas>`;
                    document.getElementById('chartContainer').appendChild(chartDiv);
                }

                for (const metricName of metricNames) {
                    if (datasets[metricName] && datasets[metricName].length > 0) {
                        if (charts[metricName]) {
                            charts[metricName].destroy();
                        }
                        charts[metricName] = updateChart(null, metricName, datasets[metricName], startDate, endDate);
                    } else {
                        console.warn(`No valid data for chart: ${metricName}`);
                    }
                }

                // Display messages
                console.log('Calling displayMessages with:', messages);
                displayMessages(messages);
            } else {
                console.error(`No data found for hostname: ${hostname}`);
                updateHostInfo(hostname, {});
                document.getElementById('chartContainer').innerHTML = '';
                Object.values(charts).forEach(chart => chart.destroy());
                charts = {};
            }
        } catch (error) {
            console.error('Error updating dashboard:', error);
            document.getElementById('chartContainer').innerHTML = '<p>Error loading dashboard data. Please try again later.</p>';
        }
    }

    if (!isRealtimeUpdate) {
        await updateRecentAlerts(hostname);
        await updateDowntimes(hostname);
        await updateAlertConfigs(hostname);
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

async function handleUpdate() {
    console.log('Update button clicked');
    const hostname = document.querySelector('#hostSelector select').value;
    await updateDashboard(hostname);
}

function initDashboard() {
    fetchHosts().then(hosts => {
        createHostSelector(hosts, updateDashboard);
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