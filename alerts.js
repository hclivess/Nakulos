// alerts.js

async function updateAlertConfigs(hostname) {
    try {
        const response = await fetch(`/alert_config?hostname=${hostname}`);
        const configs = await response.json();
        const configList = document.getElementById('alertConfigList');
        configList.innerHTML = '';
        configs.filter(config => hostname === 'all' || config.hostname === hostname).forEach(config => {
            const configDiv = document.createElement('div');
            configDiv.className = 'alert alert-secondary';
            configDiv.innerHTML = `
                <strong>${hostname === 'all' ? config.hostname + ' - ' : ''}${config.metric_name}</strong>:
                ${config.condition} ${config.threshold}
                for ${config.duration} seconds
                <div class="float-end">
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="alertEnabled_${config.id}"
                            ${config.enabled ? 'checked' : ''} onchange="toggleAlertState(${config.id}, '${config.hostname}', '${config.metric_name}', this.checked)">
                        <label class="form-check-label" for="alertEnabled_${config.id}">Enabled</label>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="deleteAlertConfig(${config.id})">Delete</button>
                </div>
            `;
            configList.appendChild(configDiv);
        });
    } catch (error) {
        console.error('Error updating alert configs:', error);
    }
}

async function addAlertConfig(event) {
    event.preventDefault();
    const alertConfig = {
        hostname: document.getElementById('hostname').value,
        metric_name: document.getElementById('metric_name').value,
        condition: document.getElementById('condition').value,
        threshold: parseFloat(document.getElementById('threshold').value),
        duration: parseInt(document.getElementById('duration').value)
    };

    try {
        const response = await fetch('/alert_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(alertConfig),
        });

        if (response.ok) {
            console.log('Alert config added successfully');
            document.getElementById('alertForm').reset();
            await updateAlertConfigs(document.querySelector('#hostSelector select').value);
        } else {
            const errorData = await response.json();
            console.error('Failed to add alert config:', errorData.error);
        }
    } catch (error) {
        console.error('Error adding alert config:', error);
    }
}

async function deleteAlertConfig(id) {
    try {
        const response = await fetch(`/alert_config`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id }),
        });

        if (response.ok) {
            console.log(`Alert config deleted for id ${id}`);
            await updateAlertConfigs(document.querySelector('#hostSelector select').value);
        } else {
            console.error('Failed to delete alert config');
        }
    } catch (error) {
        console.error('Error deleting alert config:', error);
    }
}

async function toggleAlertState(id, hostname, metric_name, enabled) {
    try {
        const response = await fetch('/alert_state', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, enabled }),
        });

        if (response.ok) {
            console.log(`Alert state updated for ${hostname} - ${metric_name}`);
        } else {
            console.error('Failed to update alert state');
        }
    } catch (error) {
        console.error('Error updating alert state:', error);
    }
}

async function updateRecentAlerts(hostname) {
    try {
        const response = await fetch(`/fetch/recent_alerts?hostname=${hostname}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const alerts = await response.json();
        console.log('Fetched recent alerts:', alerts);  // For debugging

        const alertsList = document.getElementById('recentAlertsList');
        alertsList.innerHTML = '';

        if (alerts.length === 0) {
            alertsList.innerHTML = '<div class="alert alert-info">No recent alerts.</div>';
        } else {
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-warning';
                alertDiv.innerHTML = `
                    <strong>${hostname === 'all' ? alert.hostname + ' - ' : ''}${alert.metric_name}</strong>:
                    Value ${alert.value} ${alert.condition} ${alert.threshold}
                    at ${new Date(alert.timestamp * 1000).toLocaleString()}
                `;
                alertsList.appendChild(alertDiv);
            });
        }
    } catch (error) {
        console.error('Error updating recent alerts:', error);
    }
}

function setupAlertUpdates() {
    const updateInterval = 60000; // Update every minute
    updateRecentAlerts(document.querySelector('#hostSelector select').value);
    setInterval(() => {
        updateRecentAlerts(document.querySelector('#hostSelector select').value);
    }, updateInterval);
}

window.deleteAlertConfig = deleteAlertConfig;
export { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState, updateRecentAlerts, setupAlertUpdates };