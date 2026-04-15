// static/js/cart.js
// Funcionalidad del carrito de compras

(function() {
    'use strict';

    // Función para obtener el token CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Actualizar el contador del carrito en el header
    function updateCartCount(count) {
        const cartCounts = document.querySelectorAll('.tf-cart-count, .toolbar-count');
        cartCounts.forEach(function(element) {
            element.textContent = count;
        });
    }

    // Actualizar el total del carrito
    function updateCartTotal(total) {
        const cartTotals = document.querySelectorAll('.tf-totals-total-value');
        cartTotals.forEach(function(element) {
            element.textContent = '$' + parseFloat(total).toFixed(2) + ' USD';
        });
    }

    // Cargar y mostrar los items del carrito
    function loadCartItems() {
        fetch('/cart/detail/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount(data.cart_count);
                updateCartTotal(data.cart_total);
                renderCartItems(data.items);
                loadCartRecommendations(); // Cargar recomendaciones
            }
        })
        .catch(error => {
            console.error('Error loading cart:', error);
        });
    }

    // Cargar productos recomendados
    function loadCartRecommendations() {
        fetch('/cart/recommendations/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.recommendations) {
                renderCartRecommendations(data.recommendations);
            }
        })
        .catch(error => {
            console.error('Error loading recommendations:', error);
        });
    }

    // Renderizar productos recomendados
    function renderCartRecommendations(recommendations) {
        const wrapper = document.getElementById('cart-recommendations-wrapper');
        if (!wrapper) return;

        if (recommendations.length === 0) {
            wrapper.innerHTML = '';
            return;
        }

        let html = '';
        recommendations.forEach(function(product) {
            const imageUrl = product.imagen || '/static/images/item/default-product.jpg';
            
            html += `
                <div class="swiper-slide">
                    <div class="tf-minicart-recommendations-item">
                        <div class="tf-minicart-recommendations-item-image">
                            <a href="${product.url}">
                                <img src="${imageUrl}" alt="${product.nombre}">
                            </a>
                        </div>
                        <div class="tf-minicart-recommendations-item-infos flex-grow-1">
                            <a class="title" href="${product.url}">${product.nombre}</a>
                            <div class="price">$${parseFloat(product.precio).toFixed(2)}</div>
                        </div>
                        <div class="tf-minicart-recommendations-item-quickview">
                            <a href="${product.url}" class="hover-tooltip">
                                <span class="icon icon-view"></span>
                                <span class="tooltip">View Details</span>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        });

        wrapper.innerHTML = html;

        // Reinicializar Swiper si existe
        if (typeof Swiper !== 'undefined') {
            // Destruir Swiper existente si lo hay
            const existingSwiper = document.querySelector('.tf-cart-slide')?.swiper;
            if (existingSwiper) {
                existingSwiper.destroy(true, true);
            }

            // Crear nuevo Swiper
            setTimeout(function() {
                new Swiper('.tf-cart-slide', {
                    slidesPerView: 1,
                    spaceBetween: 15,
                    pagination: {
                        el: '.cart-slide-pagination',
                        clickable: true,
                    },
                });
            }, 100);
        }
    }

    // Renderizar los items del carrito en el modal
    function renderCartItems(items) {
        const cartItemsContainer = document.querySelector('.tf-mini-cart-items');
        if (!cartItemsContainer) return;

        if (items.length === 0) {
            cartItemsContainer.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-muted">Tu carrito está vacío</p>
                </div>
            `;
            return;
        }

        let html = '';
        items.forEach(function(item) {
            const imageUrl = item.imagen || '/static/images/item/default-product.jpg';
            // Solo mostrar talla, NO color
            const variant = item.talla ? `Talla: ${item.talla}` : '';
            const stock = item.stock || 0;
            const isAtMaxStock = item.quantity >= stock;
            const isAtMinQuantity = item.quantity <= 1;
            
            // Debug: mostrar info en consola
            console.log(`📦 Renderizando: ${item.nombre}, Qty: ${item.quantity}, Stock: ${stock}, Max: ${isAtMaxStock}`);
            
            html += `
                <div class="tf-mini-cart-item" data-product-id="${item.product_id}" data-stock="${stock}">
                    <div class="tf-mini-cart-image">
                        <a href="/product/${item.producto_id}/">
                            <img src="${imageUrl}" alt="${item.nombre}">
                        </a>
                    </div>
                    <div class="tf-mini-cart-info">
                        <a class="title link" href="/product/${item.producto_id}/">${item.nombre}</a>
                        ${variant ? `<div class="meta-variant">${variant}</div>` : ''}
                        ${stock > 0 ? `<div class="meta-variant text-muted" style="font-size: 0.85rem;">Stock disponible: ${stock}</div>` : ''}
                        <div class="price fw-6">$${parseFloat(item.precio).toFixed(2)}</div>
                        <div class="tf-mini-cart-btns">
                            <div class="wg-quantity small">
                                <span class="btn-quantity minus-btn" data-action="decrease" ${isAtMinQuantity ? 'style="opacity: 0.5; cursor: not-allowed; pointer-events: none;"' : ''}>-</span>
                                <input type="text" name="number" value="${item.quantity}" readonly>
                                <span class="btn-quantity plus-btn" data-action="increase" ${isAtMaxStock ? 'style="opacity: 0.5; cursor: not-allowed; pointer-events: none;"' : ''}>+</span>
                            </div>
                            <div class="tf-mini-cart-remove" data-action="remove">Remove</div>
                        </div>
                    </div>
                </div>
            `;
        });

        cartItemsContainer.innerHTML = html;
        attachCartItemListeners();
    }

    // Adjuntar event listeners a los botones del carrito
    function attachCartItemListeners() {
        // Botones de incrementar/decrementar cantidad
        document.querySelectorAll('.tf-mini-cart-item .btn-quantity').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.tf-mini-cart-item');
                const productId = item.dataset.productId;
                const stock = parseInt(item.dataset.stock) || 0;
                const input = item.querySelector('input[name="number"]');
                let quantity = parseInt(input.value);
                const action = this.dataset.action;

                console.log(`🛒 Cart Action: ${action}, Current: ${quantity}, Stock: ${stock}`);

                if (action === 'increase') {
                    if (stock === 0) {
                        console.log('❌ No hay stock disponible');
                        return;
                    }
                    if (quantity < stock) {
                        quantity += 1;
                        console.log(`✅ Incrementado a ${quantity}`);
                    } else {
                        console.log(`❌ No se puede agregar más: stock máximo (${stock}) alcanzado`);
                        return;
                    }
                } else if (action === 'decrease') {
                    if (quantity > 1) {
                        quantity -= 1;
                        console.log(`✅ Decrementado a ${quantity}`);
                    } else {
                        console.log('❌ Cantidad mínima es 1');
                        return;
                    }
                }

                updateCartQuantity(productId, quantity);
            });
        });

        // Botones de eliminar
        document.querySelectorAll('.tf-mini-cart-remove').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const item = this.closest('.tf-mini-cart-item');
                const productId = item.dataset.productId;
                removeFromCart(productId);
            });
        });
    }

    // Agregar producto al carrito
    window.addToCart = function(productoId, varianteId, quantity) {
        quantity = quantity || 1;

        const formData = new FormData();
        formData.append('producto_id', productoId);
        if (varianteId) {
            formData.append('variante_id', varianteId);
        }
        formData.append('quantity', quantity);

        fetch('/cart/add/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount(data.cart_count);
                updateCartTotal(data.cart_total);
                loadCartItems(); // Esto también carga las recomendaciones
                
                // Mostrar el modal del carrito
                const cartModal = document.getElementById('shoppingCart');
                if (cartModal) {
                    // Usar getInstance para obtener la instancia existente o crear una nueva
                    let bsModal = bootstrap.Modal.getInstance(cartModal);
                    if (!bsModal) {
                        bsModal = new bootstrap.Modal(cartModal, {
                            backdrop: true,
                            keyboard: true,
                            focus: true
                        });
                    }
                    bsModal.show();
                }
                
                // Mostrar notificación de éxito
                showNotification('Producto agregado al carrito', 'success');
            } else {
                showNotification(data.message || 'Error al agregar el producto', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showNotification('Error al agregar el producto al carrito', 'error');
        });
    };

    // Actualizar cantidad en el carrito
    function updateCartQuantity(productId, quantity) {
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('quantity', quantity);

        fetch('/cart/update/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount(data.cart_count);
                updateCartTotal(data.cart_total);
                loadCartItems();
            }
        })
        .catch(error => {
            console.error('Error updating cart:', error);
        });
    }

    // Eliminar producto del carrito
    function removeFromCart(productId) {
        const formData = new FormData();
        formData.append('product_id', productId);

        fetch('/cart/remove/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount(data.cart_count);
                updateCartTotal(data.cart_total);
                loadCartItems(); // Esto también actualiza las recomendaciones
                showNotification('Producto eliminado del carrito', 'success');
            }
        })
        .catch(error => {
            console.error('Error removing from cart:', error);
        });
    }

    // Mostrar notificación
    function showNotification(message, type) {
        // Puedes personalizar esto con tu propio sistema de notificaciones
        console.log(`[${type}] ${message}`);
        // Aquí podrías usar una librería de toast/notifications
    }

    // Función global para limpiar backdrops residuales
    function cleanupModalBackdrops() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(function(backdrop) {
            backdrop.remove();
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    // Event listener para el botón "Add to cart" en product detail
    document.addEventListener('DOMContentLoaded', function() {
        // Cargar el carrito al inicio
        loadCartItems();

        // Listener global para limpiar backdrops cuando cualquier modal se cierra
        document.addEventListener('hidden.bs.modal', function(event) {
            // Pequeño delay para asegurar que Bootstrap termine su limpieza
            setTimeout(cleanupModalBackdrops, 100);
        });

        // Manejar click en botones "Add to cart"
        document.querySelectorAll('.btn-add-to-cart').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Obtener el producto ID desde el DOM
                const productoId = document.querySelector('[data-producto-id]')?.dataset.productoId;
                if (!productoId) {
                    showNotification('Error: No se pudo encontrar el ID del producto', 'error');
                    return;
                }

                // Obtener la variante ID desde el script de control de stock
                let varianteId = null;
                if (typeof window.currentVariantId !== 'undefined' && window.currentVariantId) {
                    varianteId = window.currentVariantId;
                } else {
                    // Fallback: buscar en inputs de variante
                    const varianteSelect = document.querySelector('input[name="variant"]:checked, select[name="variant"]');
                    if (varianteSelect) {
                        varianteId = varianteSelect.value || varianteSelect.dataset.varianteId;
                    }
                }

                // Obtener la cantidad
                const quantityInput = document.querySelector('.quantity-product, input[name="number"]');
                const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
                
                // Validar que haya stock suficiente
                if (typeof window.currentMaxStock !== 'undefined') {
                    // Si es un producto sin atributos y tiene stock definido, permitir agregar
                    if (window.currentMaxStock > 0) {
                        if (quantity > window.currentMaxStock) {
                            showNotification('Stock insuficiente. Solo hay ' + window.currentMaxStock + ' unidades disponibles.', 'error');
                            return;
                        }
                    } else if (window.currentMaxStock === 0) {
                        showNotification('Producto sin stock disponible', 'error');
                        return;
                    }
                    // Si currentMaxStock no está definido o es undefined, continuar (productos antiguos sin validación)
                }

                // Agregar al carrito
                addToCart(productoId, varianteId, quantity);
            });
        });

        // Cargar items cuando se abre el modal del carrito
        const cartModal = document.getElementById('shoppingCart');
        if (cartModal) {
            cartModal.addEventListener('show.bs.modal', function() {
                loadCartItems();
            });
            
            // Limpiar backdrop cuando se cierra el modal
            cartModal.addEventListener('hidden.bs.modal', function() {
                cleanupModalBackdrops();
            });
        }

        // Manejar el botón de agregar nota
        const btnAddNote = document.querySelector('.btn-add-note');
        if (btnAddNote) {
            btnAddNote.addEventListener('click', function() {
                document.querySelector('.add-note').classList.add('open');
            });
        }

        // Manejar el cierre del panel de nota
        document.querySelectorAll('.add-note .tf-mini-cart-tool-close').forEach(btn => {
            btn.addEventListener('click', function() {
                const notePanel = document.querySelector('.add-note');
                notePanel.classList.remove('open');
                
                // Guardar la nota
                const noteText = document.getElementById('Cart-note').value;
                if (noteText.trim()) {
                    saveCartNote(noteText);
                }
            });
        });

        // Manejar el botón de agregar gift wrap
        const btnAddGift = document.querySelector('.btn-add-gift');
        if (btnAddGift) {
            btnAddGift.addEventListener('click', function() {
                document.querySelector('.add-gift').classList.add('open');
            });
        }

        // Manejar el cierre del panel de gift wrap
        document.querySelectorAll('.add-gift .tf-mini-cart-tool-close').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelector('.add-gift').classList.remove('open');
            });
        });

        // Manejar el formulario de gift wrap
        const giftForm = document.querySelector('.tf-product-form-addgift');
        if (giftForm) {
            giftForm.addEventListener('submit', function(e) {
                e.preventDefault();
                addGiftWrap();
            });
        }
    });

    // Función para guardar la nota del carrito
    function saveCartNote(note) {
        const formData = new FormData();
        formData.append('note', note);

        fetch('/cart/save-note/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Nota guardada correctamente', 'success');
            }
        })
        .catch(error => {
            console.error('Error saving note:', error);
        });
    }

    // Función para agregar gift wrap
    function addGiftWrap() {
        fetch('/cart/add-gift-wrap/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartTotal(data.cart_total);
                document.querySelector('.add-gift').classList.remove('open');
                showNotification('Gift wrap agregado (+$5.00)', 'success');
            }
        })
        .catch(error => {
            console.error('Error adding gift wrap:', error);
        });
    }

})();
