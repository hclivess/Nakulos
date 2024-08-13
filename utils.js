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

function processMetricData(metricData, metricName) {
    const datasets = [];
    if (metricData.length > 0) {
        const firstPoint = metricData[0].value;
        const keys = Object.keys(firstPoint);
        keys.forEach((key, index) => {
            datasets.push({
                label: key,
                data: metricData.map(point => ({
                    x: new Date(point.timestamp * 1000),
                    y: point.value[key]
                })).filter(dataPoint => dataPoint.y !== null),
                borderColor: getVibrantColor(index),
                backgroundColor: getVibrantColor(index),
                fill: false
            });
        });
    }
    return datasets;
}

export { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility, createHostSelector, updateHostInfo, getVibrantColor, processMetricData, updateUrlWithHost };