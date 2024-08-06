import { initChart, updateChart } from './chart.js';
import { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState, updateRecentAlerts, setupAlertUpdates } from './alerts.js';
import { updateDowntimes, addDowntime, deleteDowntime } from './downtimes.js';
import { fetchHosts, fetchLatestMetrics, fetchMetricHistory, setTimeRange, updateFormVisibility } from './utils.js';

let chart;

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

async function updateDashboard(hostname) {
  console.log('Updating dashboard...');
  console.log('Selected hostname:', hostname);

  let charts = {};

  if (hostname === 'all') {
    document.getElementById('hostInfo').style.display = 'none';
    document.getElementById('chartContainer').innerHTML = '';
    Object.values(charts).forEach(chart => chart.destroy());
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

      const chartContainer = document.getElementById('chartContainer');
      chartContainer.innerHTML = '';

      const datasets = {};
      const fetchPromises = metricNames.map(async (metric) => {
        const metricData = await fetchMetricHistory(hostname, metric, startDate.getTime() / 1000, endDate.getTime() / 1000);
        const data = metricData.map(point => ({ x: new Date(point[0] * 1000), y: point[1] }));
        datasets[metric] = {
          label: metric,
          data: data,
          borderColor: getRandomColor(),
          fill: false
        };
      });

      await Promise.all(fetchPromises);

      for (const metric of metricNames) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'col-12';
        chartDiv.style.height = '400px'; // Set a fixed height for the chart container
        chartDiv.innerHTML = `<canvas id="${metric}Chart"></canvas>`;
        chartContainer.appendChild(chartDiv);
      }

      // Delay the chart initialization/update to ensure canvas elements are available
      setTimeout(() => {
        for (const metric of metricNames) {
          if (charts[metric]) {
            charts[metric] = updateChart(charts[metric], metric, [datasets[metric]], startDate, endDate);
          } else {
            charts[metric] = initChart(metric, [datasets[metric]]);
          }
        }
      }, 100); // Adjust the delay as needed
    } else {
      console.error(`No data found for hostname: ${hostname}`);
      updateHostInfo(hostname, {});
      document.getElementById('chartContainer').innerHTML = '';
      Object.values(charts).forEach(chart => chart.destroy());
    }
  }

  await updateRecentAlerts(hostname);
  await updateDowntimes(hostname);
  await updateAlertConfigs(hostname);
}

function getRandomColor() {
  const letters = '0123456789ABCDEF';
  let color = '#';
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

function initDashboard() {
    fetchHosts().then(hosts => {
        createHostSelector(hosts);
        setupTimeRangeButtons();
        setTimeRange('hour');
        updateDashboard('all');
        updateFormVisibility('all');
        setupAlertUpdates();
        document.getElementById('removeHostButton').addEventListener('click', removeSelectedHost);
        document.getElementById('updateButton').addEventListener('click', handleUpdate);
    });
}

function startDashboardUpdater() {
    setInterval(() => {
        const hostname = document.querySelector('#hostSelector select').value;
        updateDashboard(hostname);
    }, 60000);  // Update every minute
}

async function handleUpdate() {
    const hostname = document.querySelector('#hostSelector select').value;
    await updateDashboard(hostname);
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

export { updateDashboard, initDashboard };