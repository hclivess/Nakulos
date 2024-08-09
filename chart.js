// Utility function to generate a color based on an index
function getColor(index) {
    const colors = [
        '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
        '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
    ];
    return colors[index % colors.length];
}

// Function to initialize a new chart
function initChart(metricName, datasets, startDate, endDate) {
    const ctx = document.getElementById(`${metricName}Chart`).getContext('2d');
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
                    text: `${metricName} Metrics Over Time`
                },
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            elements: {
                line: {
                    tension: 0.1 // Slight curve on lines
                },
                point: {
                    radius: 0 // Hide points
                }
            }
        }
    });
}

// Function to update an existing chart or create a new one
function updateChart(existingChart, metricName, datasets, startDate, endDate) {
    if (existingChart) {
        existingChart.destroy();
    }
    return initChart(metricName, datasets, startDate, endDate);
}

// Function to add new data points to an existing chart
function addDataToChart(chart, newData) {
    newData.forEach(point => {
        const timestamp = new Date(point.timestamp * 1000);
        chart.data.datasets.forEach((dataset, index) => {
            const value = point[dataset.label];
            dataset.data.push({ x: timestamp, y: value });
        });
    });

    // Remove old data points if there are too many
    const maxDataPoints = 100;
    if (chart.data.datasets[0].data.length > maxDataPoints) {
        chart.data.datasets.forEach(dataset => {
            dataset.data.splice(0, dataset.data.length - maxDataPoints);
        });
    }

    chart.update();
}

// Function to update the time range of a chart
function updateChartTimeRange(chart, startDate, endDate) {
    chart.options.scales.x.min = startDate;
    chart.options.scales.x.max = endDate;
    chart.update();
}

export { initChart, updateChart, addDataToChart, updateChartTimeRange };