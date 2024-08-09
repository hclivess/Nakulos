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

    // Remove active class from all buttons
    document.querySelectorAll('.dropdown-item').forEach(btn => btn.classList.remove('active'));

    switch (range) {
        case 'realtime':
            start = new Date(end.getTime() - 5 * 60 * 1000);  // Last 5 minutes
            document.getElementById('lastRealtimeButton').classList.add('active');
            updateInterval = setInterval(() => {
                const currentEnd = new Date();
                const currentStart = new Date(currentEnd.getTime() - 5 * 60 * 1000);
                document.getElementById('endDate').value = currentEnd.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
                document.getElementById('startDate').value = currentStart.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
            }, 1000);  // Update every second
            break;
        case 'hour':
            start = new Date(end.getTime() - 60 * 60 * 1000);  // Last hour
            document.getElementById('lastHourButton').classList.add('active');
            break;
        case 'day':
            start = new Date(end.getTime() - 24 * 60 * 60 * 1000);  // Last day
            document.getElementById('lastDayButton').classList.add('active');
            break;
        case 'week':
            start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);  // Last week
            document.getElementById('lastWeekButton').classList.add('active');
            break;
        case 'month':
            start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);  // Last month
            document.getElementById('lastMonthButton').classList.add('active');
            break;
        default:
            start = new Date(end.getTime() - 60 * 60 * 1000);  // Default to last hour
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

export { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility };