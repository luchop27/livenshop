document.addEventListener('DOMContentLoaded', function() {
    var tipoSelect = document.querySelector('#id_tipo_inventario');
    var stockRow = document.querySelector('.field-stock');
    var comportamientoRow = document.querySelector('.field-comportamiento_agotamiento');

    if (!tipoSelect) return;

    function toggleInventarioFields() {
        var isInmediata = tipoSelect.value === 'ENTREGA_INMEDIATA';
        if (stockRow) stockRow.style.display = isInmediata ? '' : 'none';
        if (comportamientoRow) comportamientoRow.style.display = isInmediata ? '' : 'none';
    }

    toggleInventarioFields();
    tipoSelect.addEventListener('change', toggleInventarioFields);
});
