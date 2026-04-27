$(document).ready(function() {
    $('#quick_view').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget); // Botón que activó el modal
        var productId = button.data('product-id'); // Extrae el ID del producto
        
        console.log('DEBUG: Modal activado');
        console.log('DEBUG: Product ID:', productId);
        console.log('DEBUG: Button:', button);
        
        if (productId) {
            // Muestra loading
            $('#quickview-title').text('Cargando...');
            $('#quickview-price').text('$0.00');
            $('#quickview-description').text('Cargando descripción...');
            $('#quickview-stock').text('0');
            $('#quickview-images').html( '<div class="swiper-slide"><div class="item"><img src="' + PLACEHOLDER_IMG + '" alt="Cargando..."></div></div>'
);
            
            var url = '/api/producto/' + productId + '/quick-view/';
            console.log('DEBUG: Haciendo petición a:', url);
            
            $.get(url, function(data) {
                console.log('DEBUG: Datos recibidos:', data);
                // Pobla el modal con los datos
                $('#quickview-title').text(data.nombre);
                $('#quickview-price').text('$' + data.precio_final);
                $('#quickview-description').text(data.descripcion_corta);
                $('#quickview-stock').text(data.stock);
                $('#quickview-link').attr('href', data.url_detalle);
                
                // Imágenes en el swiper
                var imagesHtml = '';
                data.imagenes.forEach(function(img) {
                    imagesHtml += '<div class="swiper-slide"><div class="item"><img src="' + img.src + '" alt="' + img.alt + '"></div></div>';
                });
                $('#quickview-images').html(imagesHtml);
                
                // Re-inicializa el swiper si es necesario
                if (window.quickViewSwiper) {
                    window.quickViewSwiper.destroy();
                }
                window.quickViewSwiper = new Swiper('.tf-single-slide', {
                    navigation: {
                        nextEl: '.single-slide-prev',
                        prevEl: '.single-slide-next',
                    },
                    slidesPerView: 1,
                    spaceBetween: 0
                });
                
                // Variantes/atributos
                var variantsHtml = '';
                data.atributos.forEach(function(attr) {
                    variantsHtml += '<div class="variant-picker-item"><div class="variant-picker-label">' + attr.nombre + ': <span class="fw-6">' + attr.valor + '</span></div></div>';
                });
                $('#quickview-variants').html(variantsHtml);
                
                // Precio total
                $('#quickview-total-price').text('$' + data.precio_final);
                
                // Para agregar al carrito
                $('.btn-add-to-cart-quickview').data('product-id', data.id);
                
                // Mostrar badges si tiene stock
                if (data.tiene_stock) {
                    $('.tf-product-info-badges').show();
                } else {
                    $('.tf-product-info-badges').hide();
                }
                
            }).fail(function(xhr, status, error) {
                console.error('DEBUG: Error en la petición:', status, error);
                console.error('DEBUG: Respuesta:', xhr.responseText);
                alert('Error al cargar el producto. Status: ' + status);
            });
        } else {
            console.warn('DEBUG: No se encontró product-id en el botón');
        }
    });
});