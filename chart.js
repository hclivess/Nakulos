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

function updateChart(existingChart, datasets, startDate, endDate) {
    if (existingChart) {
        existingChart.destroy();
    }

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
                    },
                    min: startDate,
                    max: endDate
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
            maintainAspectRatio: false,
            spanGaps: true // This will connect points across gaps
        }
    });
}

export { initChart, updateChart };