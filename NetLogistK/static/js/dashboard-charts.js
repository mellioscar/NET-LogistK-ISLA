document.addEventListener("DOMContentLoaded", function () {
  var ctxArea = document.getElementById("myAreaChart").getContext('2d');
  
  var labelsRepartosMensuales = JSON.parse(document.getElementById("labelsRepartosMensuales").textContent.replace(/'/g, '"'));
  var dataRepartosMensuales = JSON.parse(document.getElementById("dataRepartosMensuales").textContent);

  new Chart(ctxArea, {
      type: 'line',
      data: {
          labels: labelsRepartosMensuales,
          datasets: [{
              label: "Repartos Mensuales",
              lineTension: 0.3,
              backgroundColor: "rgba(78, 115, 223, 0.05)",
              borderColor: "rgba(78, 115, 223, 1)",
              pointRadius: 3,
              pointBackgroundColor: "rgba(78, 115, 223, 1)",
              pointBorderColor: "rgba(78, 115, 223, 1)",
              pointHoverRadius: 3,
              pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
              pointHoverBorderColor: "rgba(78, 115, 223, 1)",
              pointHitRadius: 10,
              pointBorderWidth: 2,
              data: dataRepartosMensuales,
          }],
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
              x: {
                  grid: {
                      display: false,
                      drawBorder: false
                  },
                  ticks: {
                      maxTicksLimit: 12
                  }
              },
              y: {
                  ticks: {
                      maxTicksLimit: 5,
                      padding: 10,
                      callback: function(value) {
                          return value;
                      }
                  },
                  grid: {
                      color: "rgb(234, 236, 244)",
                      zeroLineColor: "rgb(234, 236, 244)",
                      drawBorder: false,
                      borderDash: [2],
                      zeroLineBorderDash: [2]
                  }
              }
          },
          plugins: {
              legend: {
                  display: false
              },
              tooltip: {
                  backgroundColor: "rgb(255,255,255)",
                  bodyColor: "#858796",
                  titleMarginBottom: 10,
                  titleColor: '#6e707e',
                  titleFont: { size: 14 },
                  borderColor: '#dddfeb',
                  borderWidth: 1,
                  xPadding: 15,
                  yPadding: 15,
                  displayColors: false,
                  intersect: false,
                  mode: 'index',
                  caretPadding: 10,
                  callbacks: {
                      label: function(tooltipItem) {
                          var datasetLabel = tooltipItem.dataset.label || '';
                          return datasetLabel + ': ' + tooltipItem.raw;
                      }
                  }
              }
          }
      }
  });
});
