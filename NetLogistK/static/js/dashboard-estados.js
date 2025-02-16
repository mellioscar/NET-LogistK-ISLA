document.addEventListener("DOMContentLoaded", function () {
    try {
        var ctx = document.getElementById("estadosRepartosChart").getContext('2d');
        
        var labels = JSON.parse(document.getElementById("labelsEstados").textContent);
        var data = JSON.parse(document.getElementById("dataEstados").textContent);

        var colores = {
            'Abierto': '#4e73df',    // text-primary
            'En Curso': '#f6c23e',    // text-warning
            'Finalizado': '#1cc88a'   // text-success
        };

        var backgroundColors = labels.map(label => colores[label]);
        var hoverColors = labels.map(label => {
            let color = colores[label];
            return color.replace(')', ', 0.8)').replace('rgb', 'rgba');
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Cantidad de Repartos',
                    data: data,
                    backgroundColor: backgroundColors,
                    hoverBackgroundColor: hoverColors,
                    borderWidth: 0,
                    borderRadius: 4,
                    barThickness: 35,
                    maxBarThickness: 50
                }]
            },
            options: {
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        left: 10,
                        right: 25,
                        top: 25,
                        bottom: 0
                    }
                },
                scales: {
                    xAxes: [{
                        gridLines: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            fontStyle: 'bold',
                            fontColor: '#858796'
                        }
                    }],
                    yAxes: [{
                        gridLines: {
                            color: "rgb(234, 236, 244)",
                            zeroLineColor: "rgb(234, 236, 244)",
                            drawBorder: false,
                            borderDash: [2],
                            zeroLineBorderDash: [2]
                        },
                        ticks: {
                            beginAtZero: true,
                            stepSize: 1,
                            fontColor: '#858796',
                            padding: 10
                        }
                    }]
                },
                legend: {
                    display: false
                },
                tooltips: {
                    titleMarginBottom: 10,
                    titleFontColor: '#6e707e',
                    titleFontSize: 14,
                    backgroundColor: "rgb(255,255,255)",
                    bodyFontColor: "#858796",
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    xPadding: 15,
                    yPadding: 15,
                    displayColors: false,
                    caretPadding: 10,
                    callbacks: {
                        label: function(tooltipItem, chart) {
                            return tooltipItem.yLabel + ' Repartos';
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error al crear el gráfico de estados:", error);
    }
}); 