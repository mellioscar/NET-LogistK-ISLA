// dashboard-charts-circular.js
document.addEventListener("DOMContentLoaded", function () {
    function actualizarGraficoCircular() {
        var ctxPie = document.getElementById("myPieChart").getContext('2d');
        
        // Obtener los datos de estado desde el backend
        var labelsEstados = JSON.parse(document.getElementById("labelsEstados").textContent.replace(/'/g, '"'));
        var dataEstados = JSON.parse(document.getElementById("dataEstados").textContent);

        new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: labelsEstados,
                datasets: [{
                    data: dataEstados,
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc'],
                    hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf'],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                }],
            },
            
            options: {
                maintainAspectRatio: false,
                tooltips: {
                    backgroundColor: "rgb(255,255,255)",
                    bodyFontColor: "#858796",
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    xPadding: 10,
                    yPadding: 10,
                    displayColors: false,
                    caretPadding: 10,
                },
                legend: {
                    display: false // Ocultar leyenda si no se necesita
                },
                cutoutPercentage: 80, // Hace el gráfico más estilo "donut"
            },
        });
    }

    actualizarGraficoCircular();
});
