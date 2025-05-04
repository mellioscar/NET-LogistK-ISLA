// Variables globales
let map;
let markers = L.markerClusterGroup();
let bounds = L.latLngBounds();

// Inicializar el mapa
function initMapa() {
    // Crear el mapa centrado en Argentina
    map = L.map('mapaTracking').setView([-34.6037, -58.3816], 12);

    // Agregar el tile layer de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Agregar el grupo de marcadores al mapa
    map.addLayer(markers);

    // Cargar marcadores iniciales
    actualizarMarcadores();
}

// Función para actualizar los marcadores
function actualizarMarcadores() {
    // Obtener los valores de los filtros
    const filtros = {
        chofer: $('#chofer').val(),
        zona: $('#zona').val(),
        estado: $('#estado').val(),
        fecha: $('#fecha').val()
    };

    // Realizar la petición AJAX
    $.ajax({
        url: '/tracking/obtener_ubicaciones/',
        data: filtros,
        success: function(response) {
            // Limpiar marcadores existentes
            markers.clearLayers();
            bounds = L.latLngBounds();

            // Agregar nuevos marcadores
            response.ubicaciones.forEach(function(ubicacion) {
                const marker = crearMarcador(ubicacion);
                markers.addLayer(marker);
                bounds.extend([ubicacion.lat, ubicacion.lng]);
            });

            // Actualizar el panel de información
            actualizarPanelInfo(response.estadisticas);

            // Centrar el mapa si hay marcadores
            if (bounds.isValid()) {
                map.fitBounds(bounds);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error al obtener ubicaciones:', error);
            mostrarError('Error al cargar las ubicaciones de los repartos');
        }
    });
}

// Función para crear un marcador
function crearMarcador(ubicacion) {
    const marker = L.marker([ubicacion.lat, ubicacion.lng], {
        icon: obtenerIconoMarcador(ubicacion.estado)
    });

    // Crear el contenido del popup
    const popupContent = `
        <div class="info-window">
            <h5>${ubicacion.chofer}</h5>
            <p><strong>Vehículo:</strong> ${ubicacion.vehiculo}</p>
            <p><strong>Zona:</strong> ${ubicacion.zona}</p>
            <p><strong>Última actualización:</strong> ${ubicacion.ultima_actualizacion}</p>
            <p><strong>Pedidos:</strong> ${ubicacion.pedidos_completados}/${ubicacion.total_pedidos}</p>
            <div class="progress mt-2" style="height: 5px;">
                <div class="progress-bar bg-info" role="progressbar" 
                     style="width: ${ubicacion.porcentaje_completado}%"></div>
            </div>
            <div class="mt-2">
                <span class="badge badge-${ubicacion.estado_clase}">${ubicacion.estado_texto}</span>
            </div>
        </div>
    `;

    marker.bindPopup(popupContent);
    return marker;
}

// Función para obtener el icono del marcador según el estado
function obtenerIconoMarcador(estado) {
    const iconoBase = {
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    };

    // Colores según estado
    const colores = {
        en_curso: 'blue',
        completado: 'green',
        pendiente: 'orange',
        detenido: 'red'
    };

    return L.icon({
        ...iconoBase,
        iconUrl: `/static/img/marker-${colores[estado] || 'blue'}.png`,
        shadowUrl: '/static/img/marker-shadow.png'
    });
}

// Función para centrar el mapa
function centrarMapa() {
    if (bounds.isValid()) {
        map.fitBounds(bounds);
    }
}

// Función para mostrar errores
function mostrarError(mensaje) {
    // Implementar según el sistema de notificaciones que uses
    alert(mensaje);
}

// Función para actualizar el panel de información
function actualizarPanelInfo(estadisticas) {
    // Actualizar estadísticas en el panel
    Object.keys(estadisticas).forEach(key => {
        const elemento = $(`#${key}`);
        if (elemento.length) {
            if (elemento.is('div.progress-bar')) {
                elemento.css('width', `${estadisticas[key]}%`);
            } else {
                elemento.text(estadisticas[key]);
            }
        }
    });
} 