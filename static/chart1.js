// donation chart
const ctxDonation = document.getElementById('donationChart').getContext('2d');

new Chart(ctxDonation, {
    type: 'doughnut',
    data: {
        labels: donationTypes,
        datasets: [{
            label: 'Donation Count',
            data: donationCounts,
            backgroundColor: [
               'rgb(107, 22, 59)','rgb(171, 41, 71)','rgb(46, 20, 114)','rgb(15, 106, 59)','rgb(58, 7, 38)'

            ]
        }]

    }
});
