// Configuración de los filtros
const configurarFiltros = () => {
    // Inicializar Select2 para los selectores
    $('.select2').select2({
        theme: 'bootstrap4',
        width: '100%',
        placeholder: 'Seleccionar...',
        allowClear: true
    });

    // Evento de cambio para todos los filtros
    $('#filtrosForm select, #filtrosForm input').on('change', function() {
        actualizarMarcadores();
    });

    // Manejar la limpieza de filtros
    $('.select2-selection__clear').on('click', function() {
        setTimeout(actualizarMarcadores, 100);
    });
};

// Función para obtener los valores de los filtros
const obtenerValoresFiltros = () => {
    return {
        chofer: $('#chofer').val(),
        zona: $('#zona').val(),
        estado: $('#estado').val(),
        fecha: $('#fecha').val()
    };
};

// Función para limpiar todos los filtros
const limpiarFiltros = () => {
    $('#filtrosForm select').val(null).trigger('change');
    $('#fecha').val(moment().format('YYYY-MM-DD'));
    actualizarMarcadores();
};

// Función para actualizar la URL con los filtros
const actualizarURL = (filtros) => {
    const params = new URLSearchParams();
    
    Object.entries(filtros).forEach(([key, value]) => {
        if (value) {
            params.set(key, value);
        }
    });

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);
};

// Función para cargar filtros desde la URL
const cargarFiltrosURL = () => {
    const params = new URLSearchParams(window.location.search);
    
    params.forEach((value, key) => {
        const elemento = $(`#${key}`);
        if (elemento.length) {
            elemento.val(value).trigger('change');
        }
    });
};

// Inicializar los filtros cuando el documento esté listo
$(document).ready(function() {
    configurarFiltros();
    cargarFiltrosURL();
}); 