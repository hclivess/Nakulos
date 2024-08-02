function initChart(datasets) {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'minute' },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Metrics Over Time'
                },
                legend: {
                    position: 'top',
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function updateChart(existingChart, datasets) {
    if (existingChart) {
        existingChart.destroy();
    }
    return initChart(datasets);
}

export { initChart, updateChart };