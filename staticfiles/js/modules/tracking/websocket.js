// Configuración del WebSocket
let socket;
const RECONNECT_TIMEOUT = 5000;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Inicializar la conexión WebSocket
const initWebSocket = () => {
    // Cerrar conexión existente si la hay
    if (socket) {
        socket.close();
    }

    // Crear nueva conexión
    socket = io(window.location.origin, {
        path: '/ws/tracking/'
    });

    // Manejar eventos del WebSocket
    configurarEventosWebSocket();
};

// Configurar los eventos del WebSocket
const configurarEventosWebSocket = () => {
    // Evento de conexión establecida
    socket.on('connect', () => {
        console.log('Conexión WebSocket establecida');
        reconnectAttempts = 0;
        
        // Suscribirse a actualizaciones según los filtros actuales
        const filtros = obtenerValoresFiltros();
        socket.emit('subscribe', filtros);
    });

    // Evento de desconexión
    socket.on('disconnect', () => {
        console.log('Conexión WebSocket perdida');
        intentarReconexion();
    });

    // Evento de error
    socket.on('error', (error) => {
        console.error('Error en WebSocket:', error);
        mostrarError('Error en la conexión de tiempo real');
    });

    // Evento de actualización de ubicación
    socket.on('ubicacion_actualizada', (data) => {
        actualizarUbicacionReparto(data);
    });

    // Evento de actualización de estado
    socket.on('estado_actualizado', (data) => {
        actualizarEstadoReparto(data);
    });

    // Evento de nuevo reparto
    socket.on('nuevo_reparto', (data) => {
        agregarNuevoReparto(data);
    });

    // Evento de reparto finalizado
    socket.on('reparto_finalizado', (data) => {
        finalizarReparto(data);
    });
};

// Función para intentar reconexión
const intentarReconexion = () => {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.log('Máximo número de intentos de reconexión alcanzado');
        mostrarError('No se pudo restablecer la conexión en tiempo real');
        return;
    }

    reconnectAttempts++;
    console.log(`Intento de reconexión ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);

    setTimeout(() => {
        initWebSocket();
    }, RECONNECT_TIMEOUT);
};

// Función para actualizar la ubicación de un reparto
const actualizarUbicacionReparto = (data) => {
    const { id, lat, lng, ultima_actualizacion } = data;
    
    // Buscar el marcador existente
    markers.eachLayer((layer) => {
        if (layer.repartoId === id) {
            // Actualizar posición
            layer.setLatLng([lat, lng]);
            
            // Actualizar información del popup
            const popup = layer.getPopup();
            if (popup) {
                const content = $(popup.getContent());
                content.find('.ultima-actualizacion').text(ultima_actualizacion);
                popup.setContent(content[0]);
            }
        }
    });
};

// Función para actualizar el estado de un reparto
const actualizarEstadoReparto = (data) => {
    const { id, estado, pedidos_completados, total_pedidos } = data;
    
    // Actualizar marcador
    markers.eachLayer((layer) => {
        if (layer.repartoId === id) {
            // Actualizar icono según estado
            layer.setIcon(obtenerIconoMarcador(estado));
            
            // Actualizar información del popup
            const popup = layer.getPopup();
            if (popup) {
                const content = $(popup.getContent());
                content.find('.estado-badge')
                    .removeClass()
                    .addClass(`badge badge-${estado}`)
                    .text(estado);
                content.find('.pedidos-info')
                    .text(`${pedidos_completados}/${total_pedidos}`);
                popup.setContent(content[0]);
            }
        }
    });

    // Actualizar panel de información
    actualizarPanelInfo({
        [`reparto_${id}_progreso`]: (pedidos_completados / total_pedidos) * 100
    });
};

// Función para agregar un nuevo reparto al mapa
const agregarNuevoReparto = (data) => {
    const marker = crearMarcador(data);
    markers.addLayer(marker);
    bounds.extend([data.lat, data.lng]);
    
    if (bounds.isValid()) {
        map.fitBounds(bounds);
    }
};

// Función para finalizar un reparto
const finalizarReparto = (data) => {
    // Remover marcador del mapa
    markers.eachLayer((layer) => {
        if (layer.repartoId === data.id) {
            markers.removeLayer(layer);
        }
    });

    // Actualizar estadísticas
    actualizarMarcadores();
};

// Inicializar WebSocket cuando el documento esté listo
$(document).ready(function() {
    initWebSocket();
}); 