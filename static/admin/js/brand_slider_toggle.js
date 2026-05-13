document.addEventListener('DOMContentLoaded', function() {
    const mostrarEnSlider = document.querySelector('#id_mostrar_en_slider');
    const imagenSliderRow = document.querySelector('.field-imagen_slider');

    if (mostrarEnSlider && imagenSliderRow) {
        function toggleImagenSlider() {
            if (mostrarEnSlider.checked) {
                imagenSliderRow.style.display = 'block';
            } else {
                imagenSliderRow.style.display = 'none';
            }
        }

        // Ejecutar al cargar
        toggleImagenSlider();

        // Ejecutar al cambiar
        mostrarEnSlider.addEventListener('change', toggleImagenSlider);
    }
});
