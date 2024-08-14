async function fetchHosts() {
    const response = await fetch('/fetch/hosts');
    const hosts = await response.json();
    console.log('Fetched hosts:', hosts);
    return hosts;
}

async function fetchLatestMetrics() {
    try {
        const response = await fetch('/fetch/latest');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const metrics = await response.json();
        console.log('Fetched latest metrics:', metrics);
        return metrics;
    } catch (error) {
        console.error('Error fetching latest metrics:', error);
        return { error: 'Failed to fetch latest metrics' };
    }
}

async function fetchMetricHistory(hostname, metricName, startDate, endDate) {
    const response = await fetch(`/fetch/history/${hostname}/${metricName}?start=${startDate}&end=${endDate}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    const history = await response.json();
    console.log(`Fetched history for ${hostname} - ${metricName}:`, history);
    return history;
}

let updateInterval;

function setTimeRange(range) {
    clearInterval(updateInterval);

    const end = new Date();
    let start;

    document.querySelectorAll('.dropdown-item').forEach(btn => btn.classList.remove('active'));

    switch (range) {
        case 'realtime':
            start = new Date(end.getTime() - 5 * 60 * 1000);
            document.getElementById('lastRealtimeButton').classList.add('active');
            updateInterval = setInterval(() => {
                const currentEnd = new Date();
                const currentStart = new Date(currentEnd.getTime() - 5 * 60 * 1000);
                document.getElementById('endDate').value = currentEnd.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
                document.getElementById('startDate').value = currentStart.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
            }, 1000);
            break;
        case 'hour':
            start = new Date(end.getTime() - 60 * 60 * 1000);
            document.getElementById('lastHourButton').classList.add('active');
            break;
        case 'day':
            start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
            document.getElementById('lastDayButton').classList.add('active');
            break;
        case 'week':
            start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);
            document.getElementById('lastWeekButton').classList.add('active');
            break;
        case 'month':
            start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);
            document.getElementById('lastMonthButton').classList.add('active');
            break;
        default:
            start = new Date(end.getTime() - 60 * 60 * 1000);
    }

    document.getElementById('endDate').value = end.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
    document.getElementById('startDate').value = start.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);

    return { start, end };
}

function updateFormVisibility(selectedHostname) {
    const hostnameField = document.getElementById('hostnameField');
    const downtimeHostnameField = document.getElementById('downtimeHostnameField');

    if (selectedHostname === 'all') {
        hostnameField.style.display = 'block';
        downtimeHostnameField.style.display = 'block';
    } else {
        hostnameField.style.display = 'none';
        downtimeHostnameField.style.display = 'none';
        document.getElementById('hostname').value = selectedHostname;
        document.getElementById('downtimeHostname').value = selectedHostname;
    }
}

function createHostSelector(hosts, updateDashboard) {
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

function getVibrantColor(index) {
    const vibrantColors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
        '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
        '#008080', '#e6beff', '#9a6324', '#fffac8', '#800000',
        '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080'
    ];
    return vibrantColors[index % vibrantColors.length];
}

function updateUrlWithHost(hostname) {
    const url = new URL(window.location);
    url.searchParams.set('host', hostname);
    window.history.pushState({}, '', url);
}

async function updateDashboard(hostname, isRealtimeUpdate = false) {
    console.log('Updating dashboard...');
    console.log('Selected hostname:', hostname);

    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    let startDate = new Date(startDateInput.value);
    let endDate = new Date(endDateInput.value);

    const activeTimeRangeButton = document.querySelector('.dropdown-item.active');
    const isCustomRange = !activeTimeRangeButton;

    if (isRealtimeUpdate && !isCustomRange) {
        endDate = new Date();
        const timeDiff = endDate - startDate;
        startDate = new Date(endDate - timeDiff);

        startDateInput.value = startDate.toISOString().slice(0, 16);
        endDateInput.value = endDate.toISOString().slice(0, 16);
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
                        const metricData = await fetchMetricHistory(hostname, metricName, startDate.getTime() / 1000, endDate.getTime() / 1000);
                        console.log(`Fetched data for ${metricName}:`, metricData);
                        datasets[metricName] = processMetricData(metricData, metricName);
                        console.log(`Processed datasets for ${metricName}:`, datasets[metricName]);

                        // Collect messages from the metric data
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

function displayMessages(messages) {
    console.log('Displaying messages:', messages);
    const messageContainer = document.getElementById('messageContainer');
    if (!messageContainer) {
        console.error('Message container not found in the DOM');
        return;
    }
    messageContainer.innerHTML = '';

    if (messages.length === 0) {
        console.log('No messages to display');
        messageContainer.innerHTML = '<p>No messages to display.</p>';
        return;
    }

    const messageList = document.createElement('ul');
    messageList.className = 'list-group';

    messages.sort((a, b) => b.timestamp - a.timestamp);  // Sort messages by timestamp, newest first

    messages.forEach(msg => {
        console.log('Creating list item for message:', msg);
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        listItem.innerHTML = `
            <strong>${msg.timestamp.toLocaleString()}</strong> -
            <span class="badge bg-secondary">${msg.metricName}</span>:
            ${msg.message}
        `;
        messageList.appendChild(listItem);
    });

    messageContainer.appendChild(messageList);
    console.log('Messages displayed successfully');
}

function processMetricData(metricData, metricName) {
    const datasets = [];
    console.log(`Processing metric data for ${metricName}:`, metricData);

    if (!Array.isArray(metricData) || metricData.length === 0) {
        console.warn(`No valid data for metric: ${metricName}`);
        return datasets;
    }

    const metrics = Object.keys(metricData[0]).filter(key => key !== 'timestamp');

    metrics.forEach((metric, index) => {
        datasets.push({
            label: metric,
            data: metricData.map(point => {
                const metricPoint = point[metric] || {};
                return {
                    x: new Date(point.timestamp * 1000),
                    y: metricPoint.value,
                    message: metricPoint.message
                };
            }).filter(dataPoint => dataPoint.y != null && !isNaN(dataPoint.y)),
            borderColor: getVibrantColor(index),
            backgroundColor: getVibrantColor(index),
            fill: false
        });
    });

    console.log(`Processed datasets for ${metricName}:`, datasets);
    return datasets;
}

export {
    fetchHosts,
    fetchLatestMetrics,
    fetchMetricHistory,
    setTimeRange,
    updateFormVisibility,
    createHostSelector,
    updateHostInfo,
    getVibrantColor,
    updateUrlWithHost,
    updateDashboard,
    displayMessages,
    processMetricData
};