F// dashboard-charts-circular.js
document.addEventListener("DOMContentLoaded", function () {
    try {
        var ctxPie = document.getElementById("myPieChart").getContext('2d');
        
        // Parsear los datos asegurándonos que son arrays válidos
        var labelsEstados = JSON.parse(document.getElementById("labelsEstados").textContent);
        var dataEstados = JSON.parse(document.getElementById("dataEstados").textContent);

        // Configurar colores que coincidan con la leyenda
        var backgroundColors = [
            '#4e73df',  // text-primary - Abierto
            '#f6c23e',  // text-warning - En Curso
            '#1cc88a'   // text-success - Finalizado
        ];

        // Pie Chart Example
        new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: labelsEstados,
                datasets: [{
                    data: dataEstados,
                    backgroundColor: backgroundColors,
                    hoverBackgroundColor: backgroundColors,
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
                    xPadding: 15,
                    yPadding: 15,
                    displayColors: false,
                    caretPadding: 10,
                },
                legend: {
                    display: false  // Ocultamos la leyenda generada por Chart.js
                },
                cutoutPercentage: 80,
            },
        });

    } catch (error) {
        console.error("Error al crear el gráfico circular:", error);
    }
});
