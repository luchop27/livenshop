document.addEventListener('DOMContentLoaded', function() {
    const mostrarEnSlider = document.querySelector('#id_mostrar_en_slider');
    const imagenSliderRow = document.querySelector('.field-imagen_slider');
    const imagenSliderMovilRow = document.querySelector('.field-imagen_slider_movil');

    if (mostrarEnSlider && (imagenSliderRow || imagenSliderMovilRow)) {
        function toggleImagenSlider() {
            const display = mostrarEnSlider.checked ? 'block' : 'none';
            if (imagenSliderRow) imagenSliderRow.style.display = display;
            if (imagenSliderMovilRow) imagenSliderMovilRow.style.display = display;
        }

        // Ejecutar al cargar
        toggleImagenSlider();

        // Ejecutar al cambiar
        mostrarEnSlider.addEventListener('change', toggleImagenSlider);
    }
});
