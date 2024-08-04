async function updateAlertConfigs(hostname) {
    try {
        const response = await fetch('/alert_config');
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
                    <button class="btn btn-danger btn-sm" onclick="deleteAlertConfig('${config.hostname}', '${config.metric_name}')">Delete</button>
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
            await updateAlertConfigs();  // Refresh the list of alerts
        } else {
            const errorData = await response.json();
            console.error('Failed to add alert config:', errorData.error);
        }
    } catch (error) {
        console.error('Error adding alert config:', error);
    }
}

async function deleteAlertConfig(hostname, metric_name) {
    try {
        const response = await fetch('/alert_config', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ hostname, metric_name }),
        });

        if (response.ok) {
            console.log(`Alert config deleted for ${hostname} - ${metric_name}`);
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
            body: JSON.stringify({ hostname, metric_name, enabled }),
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

export { updateAlertConfigs, addAlertConfig, deleteAlertConfig, toggleAlertState };