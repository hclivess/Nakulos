async function fetchHosts() {
    const response = await fetch('/fetch/hosts');
    const hosts = await response.json();
    console.log('Fetched hosts:', hosts);
    return hosts;
}

async function fetchLatestMetrics() {
    const response = await fetch('/fetch/latest');
    const metrics = await response.json();
    console.log('Fetched latest metrics:', metrics);
    return metrics;
}

async function fetchMetricHistory(hostname, metricName, startDate, endDate) {
    const response = await fetch(`/fetch/history/${hostname}/${metricName}?start=${startDate}&end=${endDate}`);
    const history = await response.json();
    console.log(`Fetched history for ${hostname} - ${metricName}:`, history);
    return history;
}


function setTimeRange(range) {
    const end = new Date();
    let start;

    switch (range) {
        case 'hour':
            start = new Date(end.getTime() - 60 * 60 * 1000);  // 1 hour ago
            break;
        case 'day':
            start = new Date(end.getTime() - 24 * 60 * 60 * 1000);  // 1 day ago
            break;
        case 'week':
            start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000);  // 1 week ago
            break;
        case 'month':
            start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000);  // 1 month ago
            break;
    }

    document.getElementById('endDate').value = end.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
    document.getElementById('startDate').value = start.toLocaleString('sv-SE').replace(' ', 'T').slice(0, 16);
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