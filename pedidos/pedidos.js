const API_KEY_GOOGLE = '{{ google_api_key }}';  // Esta variable será inyectada desde Django

function verificarUbicacion(direccionCompleta) {
    // Geocodificar la dirección
    $.get(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(direccionCompleta)}&key=${API_KEY_GOOGLE}`, function(response) {
        if (response.results && response.results.length > 0) {
            const location = response.results[0].geometry.location;
            
            // Inicializar el mapa
            const map = new google.maps.Map(document.getElementById('verification-map'), {
                center: location,
                zoom: 15
            });

            // Agregar marcador
            new google.maps.Marker({
                position: location,
                map: map
            });

            // Mostrar el modal
            $('#verificarUbicacionModal').modal('show');
        }
    });
}