async function updateDowntimes(hostname) {
    try {
        const response = await fetch(`/downtime?hostname=${hostname}`);
        const downtimes = await response.json();
        const downtimeList = document.getElementById('downtimeList');
        downtimeList.innerHTML = '';
        if (downtimes.length === 0) {
            downtimeList.innerHTML = '<div class="alert alert-info">No downtimes scheduled.</div>';
        } else {
            downtimes.forEach(downtime => {
                const downtimeDiv = document.createElement('div');
                downtimeDiv.className = 'alert alert-info';
                downtimeDiv.innerHTML = `
                    <strong>${hostname === 'all' ? downtime.hostname + ': ' : ''}</strong>
                    ${new Date(downtime.start_time * 1000).toLocaleString()} -
                    ${new Date(downtime.end_time * 1000).toLocaleString()}
                    <button class="btn btn-danger btn-sm float-end" onclick="deleteDowntime(${downtime.id})">Delete</button>
                `;
                downtimeList.appendChild(downtimeDiv);
            });
        }
    } catch (error) {
        console.error('Error updating downtimes:', error);
    }
}

async function addDowntime(event) {
    event.preventDefault();
    const hostname = document.querySelector('#hostSelector select').value;
    const downtimeConfig = {
        hostname: hostname === 'all' ? document.getElementById('downtimeHostname').value : hostname,
        start_time: new Date(document.getElementById('downtimeStart').value).getTime() / 1000,
        end_time: new Date(document.getElementById('downtimeEnd').value).getTime() / 1000
    };

    try {
        const response = await fetch('/downtime', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(downtimeConfig),
        });

        if (response.ok) {
            console.log('Downtime added successfully');
            document.getElementById('downtimeForm').reset();
        } else {
            console.error('Failed to add downtime');
        }
    } catch (error) {
        console.error('Error adding downtime:', error);
    }
}

async function deleteDowntime(id) {
    try {
        const response = await fetch('/downtime', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id }),
        });

        if (response.ok) {
            console.log(`Downtime deleted for id ${id}`);
            await updateDowntimes(document.querySelector('#hostSelector select').value);
        } else {
            console.error('Failed to delete downtime');
        }
    } catch (error) {
        console.error('Error deleting downtime:', error);
    }
}

export { updateDowntimes, addDowntime, deleteDowntime };