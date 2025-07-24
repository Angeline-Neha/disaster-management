const ctxDisaster = document.getElementById('disasterChart').getContext('2d');

// Create gradients before chart initialization
const gradients = [
    createGradient(ctxDisaster, ' #4B1712', ' #7B241C'),  // Deep Burgundy
    createGradient(ctxDisaster, 'rgb(114, 20, 80)', 'rgb(116, 8, 76)'),  // Wine Red
    createGradient(ctxDisaster, 'rgb(93, 40, 94)', 'rgb(140, 20, 138)'),  // Muted Plum
    createGradient(ctxDisaster, 'rgb(13, 80, 132)', 'rgb(66, 8, 107)'),  // Aubergine
    createGradient(ctxDisaster, 'rgb(3, 56, 41)', 'rgb(12, 86, 48)')   // Crimson
];

function createGradient(ctx, startColor, endColor) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, startColor);
    gradient.addColorStop(1, endColor);
    return gradient;
}

new Chart(ctxDisaster, {
    type: 'bar',
    data: {
        labels: disasterLabels,
        datasets: [{
            label: 'Number of Disasters',
            data: disasterCounts,
            backgroundColor: gradients,
            borderColor: [
                'rgb(17, 2, 1)',
                'rgb(22, 1, 4)',
                'rgb(20, 1, 7)',
                'rgb(31, 2, 19)',
                'rgb(18, 1, 2)'
            ],
            borderWidth: 1,
            borderRadius: 4,
            borderSkipped: false
        }]
    },
    options: {
        responsive: true,
        animation: {
            duration: 1000,  // Set fixed animation duration
            onComplete: () => {
                // Gradients already created, no need to regenerate
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: '#5a0035',
                    font: {
                        weight: 'bold'
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1,
                    color: '#5a0035'
                },
                grid: {
                    color: 'rgba(90, 0, 53, 0.1)'
                }
            },
            x: {
                ticks: {
                    color: '#5a0035'
                },
                grid: {
                    display: false
                }
            }
        }
    }
});

