$(document).ready(function()
{
    var ctx = document.getElementById('myChart');
    Chart.scaleService.updateScaleDefaults('linear', {
            ticks: {
                min: 0
            }
        });

    var data = {
        labels : {{ date }},
        datasets : [
            {
                label : 'product 1',
                data : {{ data }},
                backgroundColor : "blue",
                borderColor : "lightblue",
                fill : false,
                lineTension : 0
            }
            ]
    };
    var myLineChart = new Chart(ctx, {
        type: 'line',
        data:
            {
            datasets: [{
                data: {{ sells }},
                fill: false,
                backgroundColor: "blue",
                borderColor: ["rgba(54, 162, 235, 0.2)"]
            }],
            labels: [{{ date }}]// labels: ['January', 'February']
        },
        options: {
        scales: {
            xAxes: [{
                type: 'category',
                labels: [{{ date }}]
            }]
        }
    }
    });
});