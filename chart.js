function initChart(metric, datasets) {
    const ctx = document.getElementById(`${metric}Chart`).getContext('2d');
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
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 20
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${metric} Over Time`
                },
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 20,
                        boxHeight: 2
                    }
                }
            },
            layout: {
                padding: {
                    top: 20,
                    bottom: 20,
                    left: 20,
                    right: 20
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            spanGaps: true
        }
    });
}

function updateChart(existingChart, metric, datasets, startDate, endDate) {
    if (existingChart) {
        existingChart.destroy();
    }

    const ctx = document.getElementById(`${metric}Chart`).getContext('2d');
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
                    max: endDate,
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 20
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${metric} Over Time`
                },
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 20,
                        boxHeight: 2
                    }
                }
            },
            layout: {
                padding: {
                    top: 20,
                    bottom: 20,
                    left: 20,
                    right: 20
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            spanGaps: true
        }
    });
}

export { initChart, updateChart };