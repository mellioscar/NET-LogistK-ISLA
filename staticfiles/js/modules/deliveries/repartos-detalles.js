function verDetallesReparto(nroReparto) {
    $('#tablaPedidosBody').html('<tr><td colspan="4" class="text-center"><i class="fas fa-spinner fa-spin"></i> Cargando...</td></tr>');
    $('#modalDetallesReparto').modal('show');
    
    fetch(`/obtener_detalles_reparto/${encodeURIComponent(nroReparto)}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Actualizar datos del reparto
            $('#modalNroReparto').text(data.reparto.nro_reparto);
            $('#modalEstado').html(`<span class="badge badge-${data.reparto.estado_color}">${data.reparto.estado}</span>`);
            $('#modalFecha').text(data.reparto.fecha);
            $('#modalChofer').text(data.reparto.chofer);
            $('#modalZona').text(data.reparto.zona);
            $('#modalZonaDescripcion').text(data.reparto.zona_descripcion);
            
            // Actualizar tabla de pedidos
            let pedidosHtml = '';
            if (data.pedidos && data.pedidos.length > 0) {
                data.pedidos.forEach(pedido => {
                    pedidosHtml += `
                        <tr>
                            <td>${pedido.nro_factura}</td>
                            <td>${pedido.cliente}</td>
                            <td>${pedido.direccion}</td>
                            <td><span class="badge badge-${pedido.estado_color}">${pedido.estado}</span></td>
                        </tr>
                    `;
                });
            } else {
                pedidosHtml = '<tr><td colspan="4" class="text-center">No hay pedidos asignados</td></tr>';
            }
            $('#tablaPedidosBody').html(pedidosHtml);
        })
        .catch(error => {
            console.error('Error:', error);
            $('#tablaPedidosBody').html('<tr><td colspan="4" class="text-center text-danger">Error al cargar los datos</td></tr>');
        });
} 