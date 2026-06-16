// Variables globales para el stock del producto en el quickview
window._qvMaxStock = 0;
window._qvTipoInventario = 'BAJO_PEDIDO';

$(document).ready(function() {
    $('#quick_view').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var productId = button.data('product-id');

        // Reset cantidad al abrir
        var qvInput = document.querySelector('#quick_view input[name="number"]');
        if (qvInput) qvInput.value = 1;
        window._qvMaxStock = 0;
        window._qvTipoInventario = 'BAJO_PEDIDO';
        document.getElementById('quickview-delivery-badge').innerHTML = '';

        if (!productId) return;

        // Loading state
        $('#quickview-title').text('Cargando...');
        $('#quickview-price').text('$0.00');
        $('#quickview-description').text('');
        $('#quickview-images').html('<div class="swiper-slide"><div class="item"><img src="' + PLACEHOLDER_IMG + '" alt="Cargando..."></div></div>');

        $.get('/api/producto/' + productId + '/quick-view/', function(data) {
            $('#quickview-title').text(data.nombre);
            $('#quickview-price').text('$' + data.precio_final);
            $('#quickview-description').text(data.descripcion_corta);
            $('#quickview-link').attr('href', data.url_detalle);
            $('#quickview-total-price').text('$' + data.precio_final);
            $('.btn-add-to-cart-quickview').data('product-id', data.id);

            // Guardar stock y tipo para el cap
            window._qvMaxStock = data.stock || 0;
            window._qvTipoInventario = data.tipo_inventario || 'BAJO_PEDIDO';

            // Badge de tipo de entrega
            var badgeEl = document.getElementById('quickview-delivery-badge');
            if (badgeEl) {
                if (data.tipo_inventario === 'ENTREGA_INMEDIATA') {
                    badgeEl.innerHTML = '<div style="display:inline-flex;align-items:center;gap:8px;padding:8px 14px;background:#f0faf4;border:1px solid #c3e6cb;border-radius:6px;">' +
                        '<span style="width:8px;height:8px;border-radius:50%;background:#28a745;display:inline-block;flex-shrink:0;"></span>' +
                        '<span style="font-size:13px;font-weight:600;color:#1a6e3c;">Entrega Inmediata</span>' +
                        '</div>';
                } else {
                    badgeEl.innerHTML = '<div style="display:inline-flex;align-items:center;gap:8px;padding:8px 14px;background:#f4f6f9;border:1px solid #d1d9e0;border-radius:6px;">' +
                        '<span style="width:8px;height:8px;border-radius:50%;background:#0C2038;display:inline-block;flex-shrink:0;"></span>' +
                        '<span style="font-size:13px;font-weight:600;color:#0C2038;">Bajo Pedido</span>' +
                        '<span style="font-size:13px;color:#555;">— Disponible para encargo</span>' +
                        '</div>';
                }
            }

            // Imágenes
            var imagesHtml = '';
            data.imagenes.forEach(function(img) {
                imagesHtml += '<div class="swiper-slide"><div class="item"><img src="' + img.src + '" alt="' + img.alt + '"></div></div>';
            });
            $('#quickview-images').html(imagesHtml);

            if (window.quickViewSwiper) window.quickViewSwiper.destroy();
            window.quickViewSwiper = new Swiper('.tf-single-slide', {
                navigation: { nextEl: '.single-slide-prev', prevEl: '.single-slide-next' },
                slidesPerView: 1,
                spaceBetween: 0
            });

            // Atributos
            var variantsHtml = '';
            data.atributos.forEach(function(attr) {
                variantsHtml += '<div class="variant-picker-item"><div class="variant-picker-label">' + attr.nombre + ': <span class="fw-6">' + attr.valor + '</span></div></div>';
            });
            $('#quickview-variants').html(variantsHtml);

            // Wishlist
            var wishlistBtn = $('#quick_view .tf-product-btn-wishlist');
            wishlistBtn.attr('data-product-id', data.id);
            if (data.en_wishlist) {
                wishlistBtn.addClass('active');
                wishlistBtn.find('.tooltip').text('Quitar de Favoritos');
            } else {
                wishlistBtn.removeClass('active');
                wishlistBtn.find('.tooltip').text('Agregar a Favoritos');
            }

        }).fail(function() {
            $('#quickview-title').text('Error al cargar el producto.');
        });
    });

    // Resetear al cerrar
    $('#quick_view').on('hidden.bs.modal', function () {
        window._qvMaxStock = 0;
        window._qvTipoInventario = 'BAJO_PEDIDO';
        var qvInput = document.querySelector('#quick_view input[name="number"]');
        if (qvInput) qvInput.value = 1;
    });
});

// Interceptar el + del quickview antes que main.js (capture phase)
(function() {
    var modal = document.getElementById('quick_view');
    if (!modal) return;

    modal.addEventListener('click', function(e) {
        var plusBtn = e.target.closest('.plus-btn');
        if (!plusBtn) return;
        if (window._qvTipoInventario !== 'ENTREGA_INMEDIATA') return;
        if (window._qvMaxStock <= 0) return;

        var input = modal.querySelector('input[name="number"]');
        if (!input) return;
        var currentQty = parseInt(input.value) || 1;
        if (currentQty >= window._qvMaxStock) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
        }
    }, true); // capture phase — se ejecuta antes que jQuery/main.js
})();
