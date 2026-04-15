
    // Quick View JavaScript con Sistema de Atributos
    (function() {
        'use strict';
        
        // Variable global para prevenir múltiples ejecuciones
        let isProcessingQuickView = false;

        // Obtener CSRF token
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

        document.addEventListener('DOMContentLoaded', function() {
            console.log('Quick View: Script cargado');
            
            // Manejar click en botón Quick View
            document.querySelectorAll('.quickview').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log('Quick View: Botón clickeado');
                    
                    const productoId = this.getAttribute('data-producto-id');
                    console.log('Quick View: Producto ID =', productoId);
                    
                    if (!productoId) {
                        console.error('Quick View: No se pudo obtener el ID del producto');
                        alert('Error: No se pudo identificar el producto');
                        return;
                    }
                    
                    loadProductQuickView(productoId);
                });
            });

            // Manejar botones de cantidad en el modal
            const modal = document.getElementById('quick_view');
            if (modal) {
                // Event listener para reiniciar cuando se abre el modal
                modal.addEventListener('shown.bs.modal', function() {
                    const quantityInput = this.querySelector('input[name="number"]');
                    if (quantityInput) {
                        quantityInput.value = 1;
                        updateQuickViewButtons();
                        updateQuickViewPrice();
                        console.log('Modal abierto - cantidad reiniciada a 1');
                    }
                });
                
                const minusBtn = modal.querySelector('.minus-btn');
                const plusBtn = modal.querySelector('.plus-btn');
                const quantityInput = modal.querySelector('input[name="number"]');
                
                if (minusBtn && plusBtn && quantityInput) {
                    // Event listener para botón de incremento con protección contra múltiples ejecuciones
                    plusBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        // Prevenir procesamiento múltiple
                        if (isProcessingQuickView) {
                            console.log('QuickView - Ya procesando, ignorando click adicional');
                            return false;
                        }
                        
                        // Verificar si el botón está deshabilitado
                        if (this.classList.contains('disabled') || this.style.pointerEvents === 'none') {
                            console.log('QuickView - Botón + está deshabilitado');
                            return false;
                        }
                        
                        isProcessingQuickView = true;
                        
                        const currentQty = parseInt(quantityInput.value) || 1;
                        const maxStock = parseInt(modal.dataset.maxStock) || 0;
                        
                        console.log('=== QuickView INCREMENTO ===');
                        console.log('Cantidad actual:', currentQty);
                        console.log('Stock máximo:', maxStock);
                        
                        // Validación estricta: solo incrementar si hay stock disponible
                        if (currentQty < maxStock && maxStock > 0) {
                            const newQty = currentQty + 1;
                            console.log('Intentando incrementar a:', newQty);
                            
                            // Triple verificación antes de asignar
                            if (newQty <= maxStock) {
                                quantityInput.value = newQty;
                                console.log('✅ Cantidad actualizada a:', newQty);
                                updateQuickViewButtons();
                                updateQuickViewPrice();
                            } else {
                                console.log('❌ Bloqueado: excedería stock máximo');
                            }
                        } else {
                            console.log('❌ Bloqueado: ya en stock máximo');
                        }
                        
                        // Liberar el flag después de un pequeño delay
                        setTimeout(() => {
                            isProcessingQuickView = false;
                        }, 100);
                        
                        return false;
                    }, { capture: true });
                    
                    // Event listener para botón de decremento
                    minusBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        // Prevenir procesamiento múltiple
                        if (isProcessingQuickView) {
                            return false;
                        }
                        
                        // Verificar si el botón está deshabilitado
                        if (this.classList.contains('disabled') || this.style.pointerEvents === 'none') {
                            console.log('QuickView - Botón - está deshabilitado');
                            return false;
                        }
                        
                        isProcessingQuickView = true;
                        
                        const currentQty = parseInt(quantityInput.value) || 1;
                        console.log('=== QuickView DECREMENTO ===');
                        console.log('Cantidad actual:', currentQty);
                        
                        if (currentQty > 1) {
                            quantityInput.value = currentQty - 1;
                            console.log('✅ Cantidad decrementada a:', currentQty - 1);
                            updateQuickViewButtons();
                            updateQuickViewPrice();
                        }
                        
                        setTimeout(() => {
                            isProcessingQuickView = false;
                        }, 100);
                        
                        return false;
                    }, { capture: true });
                }

                // Manejar cambio de atributos
                modal.addEventListener('change', function(e) {
                    if (e.target.type === 'radio' && e.target.name.startsWith('atributo_')) {
                        updateVariantByAttributes();
                    }
                });

                // Manejar botón Add to Cart del Quick View
                const addToCartBtn = modal.querySelector('.btn-add-to-cart-quickview');
                if (addToCartBtn) {
                    addToCartBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        addToCartFromQuickView();
                    });
                }
            }
        });

        function loadProductQuickView(productId) {
            console.log('Quick View: Cargando producto ID =', productId);
            showQuickViewLoading();
            
            fetch(`/productos/api/${productId}/quick-view/`)
                .then(response => {
                    console.log('Quick View: Respuesta recibida, status =', response.status);
                    if (!response.ok) {
                        throw new Error('Error al cargar el producto');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Quick View: Datos recibidos =', data);
                    populateQuickView(data);
                })
                .catch(error => {
                    console.error('Quick View: Error =', error);
                    showQuickViewError();
                });
        }

        function showQuickViewLoading() {
            document.getElementById('quickview-title').textContent = 'Cargando...';
            document.getElementById('quickview-price').textContent = '$0.00';
            document.getElementById('quickview-description').textContent = 'Cargando descripción...';
            document.getElementById('quickview-stock').textContent = '0';
            document.getElementById('quickview-variants').innerHTML = '';
        }

        function showQuickViewError() {
            document.getElementById('quickview-title').textContent = 'Error al cargar el producto';
            document.getElementById('quickview-description').textContent = 'Por favor, intenta de nuevo más tarde.';
        }

        function populateQuickView(data) {
            const modal = document.getElementById('quick_view');
            
            // Guardar datos del producto en el modal
            modal.dataset.productoId = data.id;
            modal.dataset.basePrice = data.precio;
            modal.dataset.maxStock = data.stock || 0;  // ❌ CAMBIO: Usar 0 en lugar de 999
            modal.dataset.variantes = JSON.stringify(data.variantes);
            modal.dataset.atributos = JSON.stringify(data.atributos);
            modal.dataset.variantesStock = JSON.stringify(data.variantes_stock || {});
            modal.dataset.varianteDefaultId = data.variante_default_id || '';
            
            console.log('🔍 QuickView - Datos iniciales:', {
                productoId: data.id,
                precio: data.precio,
                stock: data.stock,
                maxStock: modal.dataset.maxStock
            });
            
            // Título
            document.getElementById('quickview-title').textContent = data.nombre;
            
            // Precio
            document.getElementById('quickview-price').textContent = `$${data.precio}`;
            document.getElementById('quickview-total-price').textContent = `$${data.precio}`;
            
            // Stock
            document.getElementById('quickview-stock').textContent = data.stock || '0';
            
            // Descripción
            document.getElementById('quickview-description').textContent = 
                data.descripcion_corta || data.descripcion_larga || 'Sin descripción disponible';
            
            // Imágenes
            const imagesContainer = document.getElementById('quickview-images');
            imagesContainer.innerHTML = '';
            
            if (data.imagenes && data.imagenes.length > 0) {
                data.imagenes.forEach(imagen => {
                    const slide = document.createElement('div');
                    slide.className = 'swiper-slide';
                    slide.innerHTML = `
                        <div class="item">
                            <img src="${imagen.src}" alt="${data.nombre}">
                        </div>
                    `;
                    imagesContainer.appendChild(slide);
                });
            } else {
                imagesContainer.innerHTML = `
                    <div class="swiper-slide">
                        <div class="item">
                            <img src="/static/images/products/placeholder.jpg" alt="${data.nombre}">
                        </div>
                    </div>
                `;
            }
            
            // Renderizar atributos
            const variantsContainer = document.getElementById('quickview-variants');
            variantsContainer.innerHTML = '';
            
            // ========== NUEVO: Para productos sin atributos (default variant) ==========
            if (data.variante_default_id) {
                // Este es un producto sin atributos (ej: Reloj, Accesorios)
                // Usar la variante default automáticamente
                const variantesStock = data.variantes_stock || {};
                if (variantesStock['default']) {
                    modal.dataset.selectedVariantId = variantesStock['default'].id;
                    modal.dataset.basePrice = variantesStock['default'].precio;
                    modal.dataset.maxStock = variantesStock['default'].stock;
                    document.getElementById('quickview-price').textContent = `$${variantesStock['default'].precio}`;
                    document.getElementById('quickview-stock').textContent = variantesStock['default'].stock;
                    console.log('✅ Quick View: Producto sin atributos - Variante DEFAULT activada:');
                    console.log('  - ID:', variantesStock['default'].id);
                    console.log('  - Stock:', variantesStock['default'].stock);
                    console.log('  - Precio:', variantesStock['default'].precio);
                }
                updateQuickViewPrice();
                return; // No renderizar atributos
            }
            // ========================================================================
            
            if (data.atributos && data.atributos.length > 0) {
                data.atributos.forEach((atributo, index) => {
                    const atributoDiv = document.createElement('div');
                    atributoDiv.className = 'variant-picker-item';
                    
                    const valoresArray = Object.values(atributo.valores);
                    
                    if (atributo.tipo === 'color') {
                        // Renderizar colores con círculos
                        atributoDiv.innerHTML = `
                            <div class="variant-picker-label">
                                ${atributo.nombre}: <span class="fw-6 variant-picker-label-value">Selecciona</span>
                            </div>
                            <div class="variant-picker-values">
                                ${valoresArray.map((valor, vIndex) => `
                                    <input type="radio" 
                                           name="atributo_${atributo.id}" 
                                           id="qv-attr-${atributo.id}-${valor.id}" 
                                           value="${valor.id}"
                                           data-atributo-slug="${atributo.slug}"
                                           ${vIndex === 0 ? 'checked' : ''}>
                                    <label class="hover-tooltip radius-60" 
                                           for="qv-attr-${atributo.id}-${valor.id}"
                                           data-value="${valor.valor}">
                                        <span class="btn-checkbox ${valor.codigo_color ? '' : 'bg-color-' + valor.valor.toLowerCase()}" 
                                              ${valor.codigo_color ? `style="background-color: ${valor.codigo_color};"` : ''}></span>
                                        <span class="tooltip">${valor.valor}</span>
                                    </label>
                                `).join('')}
                            </div>
                        `;
                    } else {
                        // Renderizar tallas u otros atributos como texto
                        atributoDiv.innerHTML = `
                            <div class="variant-picker-label">
                                ${atributo.nombre}: <span class="fw-6 variant-picker-label-value">Selecciona</span>
                            </div>
                            <div class="variant-picker-values">
                                ${valoresArray.map((valor, vIndex) => `
                                    <input type="radio" 
                                           name="atributo_${atributo.id}" 
                                           id="qv-attr-${atributo.id}-${valor.id}" 
                                           value="${valor.id}"
                                           data-atributo-slug="${atributo.slug}"
                                           ${vIndex === 0 ? 'checked' : ''}>
                                    <label class="style-text" 
                                           for="qv-attr-${atributo.id}-${valor.id}"
                                           data-value="${valor.valor}">
                                        <p>${valor.valor}</p>
                                    </label>
                                `).join('')}
                            </div>
                        `;
                    }
                    
                    variantsContainer.appendChild(atributoDiv);
                });
                
                // Actualizar variante inicial
                updateVariantByAttributes();
            }
            
            // Link a detalles completos
            document.getElementById('quickview-link').href = `/product/${data.id}/`;
            
            // Reiniciar cantidad a 1
            modal.querySelector('input[name="number"]').value = 1;
            updateQuickViewPrice();
        }

        function updateVariantByAttributes() {
            const modal = document.getElementById('quick_view');
            const variantes = JSON.parse(modal.dataset.variantes || '[]');
            const atributos = JSON.parse(modal.dataset.atributos || '[]');
            
            // Obtener atributos seleccionados
            const selectedAttrs = {};
            atributos.forEach(atributo => {
                const selectedInput = modal.querySelector(`input[name="atributo_${atributo.id}"]:checked`);
                if (selectedInput) {
                    const valorId = parseInt(selectedInput.value);
                    selectedAttrs[atributo.slug] = valorId;
                    
                    // Actualizar label
                    const label = selectedInput.closest('.variant-picker-item').querySelector('.variant-picker-label-value');
                    if (label) {
                        label.textContent = selectedInput.nextElementSibling.dataset.value;
                    }
                }
            });
            
            // Buscar variante que coincida
            const matchingVariant = variantes.find(variante => {
                return Object.keys(selectedAttrs).every(slug => {
                    const varianteAttr = variante.atributos[slug];
                    return varianteAttr && varianteAttr.valor_id === selectedAttrs[slug];
                });
            });
            
            if (matchingVariant) {
                modal.dataset.selectedVariantId = matchingVariant.id;
                modal.dataset.basePrice = matchingVariant.precio;
                modal.dataset.maxStock = matchingVariant.stock;
                document.getElementById('quickview-price').textContent = `$${matchingVariant.precio}`;
                document.getElementById('quickview-stock').textContent = matchingVariant.stock;
                
                console.log('🔄 Variante actualizada:', {
                    id: matchingVariant.id,
                    stock: matchingVariant.stock,
                    precio: matchingVariant.precio,
                    modalMaxStock: modal.dataset.maxStock
                });
                
                // Ajustar cantidad si excede el nuevo stock
                const quantityInput = modal.querySelector('input[name="number"]');
                const currentQty = parseInt(quantityInput.value) || 1;
                if (currentQty > matchingVariant.stock) {
                    quantityInput.value = matchingVariant.stock > 0 ? matchingVariant.stock : 1;
                    console.log('⚠️ Cantidad ajustada de', currentQty, 'a', quantityInput.value);
                }
                if (matchingVariant.stock === 0) {
                    quantityInput.value = 1;
                }
            } else {
                const basePrice = modal.dataset.basePrice;
                document.getElementById('quickview-price').textContent = `$${basePrice}`;
                modal.dataset.selectedVariantId = '';
                modal.dataset.maxStock = 0;
                console.log('❌ No se encontró variante coincidente');
            }
            
            updateQuickViewButtons();
            updateQuickViewPrice();
        }

        function updateQuickViewPrice() {
            const modal = document.getElementById('quick_view');
            const quantity = parseInt(modal.querySelector('input[name="number"]').value);
            const basePrice = parseFloat(modal.dataset.basePrice);
            
            if (!isNaN(basePrice) && !isNaN(quantity)) {
                const totalPrice = (basePrice * quantity).toFixed(2);
                document.getElementById('quickview-total-price').textContent = `$${totalPrice}`;
            }
        }
        
        // Función para actualizar el estado de los botones de cantidad en quickview
        function updateQuickViewButtons() {
            const modal = document.getElementById('quick_view');
            const quantityInput = modal.querySelector('input[name="number"]');
            const btnIncrease = modal.querySelector('.plus-btn');
            const btnDecrease = modal.querySelector('.minus-btn');
            
            const currentQty = parseInt(quantityInput.value) || 1;
            const maxStock = parseInt(modal.dataset.maxStock) || 0;
            
            console.log('QuickView - Actualizando botones:', {currentQty, maxStock});
            
            // Deshabilitar botón de incremento si llegamos al stock máximo o no hay stock
            if (currentQty >= maxStock || maxStock === 0) {
                btnIncrease.classList.add('disabled');
                btnIncrease.style.opacity = '0.5';
                btnIncrease.style.cursor = 'not-allowed';
                btnIncrease.style.pointerEvents = 'none';
            } else {
                btnIncrease.classList.remove('disabled');
                btnIncrease.style.opacity = '1';
                btnIncrease.style.cursor = 'pointer';
                btnIncrease.style.pointerEvents = 'auto';
            }
            
            // Deshabilitar botón de decremento si estamos en 1
            if (currentQty <= 1) {
                btnDecrease.classList.add('disabled');
                btnDecrease.style.opacity = '0.5';
                btnDecrease.style.cursor = 'not-allowed';
                btnDecrease.style.pointerEvents = 'none';
            } else {
                btnDecrease.classList.remove('disabled');
                btnDecrease.style.opacity = '1';
                btnDecrease.style.cursor = 'pointer';
                btnDecrease.style.pointerEvents = 'auto';
            }
        }

        function addToCartFromQuickView() {
            const modal = document.getElementById('quick_view');
            const productoId = modal.dataset.productoId;
            const variantId = modal.dataset.selectedVariantId;
            const quantity = parseInt(modal.querySelector('input[name="number"]').value);
            const maxStock = parseInt(modal.dataset.maxStock) || 0;
            
            if (!productoId) {
                alert('Error: No se pudo identificar el producto');
                return;
            }

            if (!variantId) {
                alert('Por favor, selecciona todas las opciones del producto');
                return;
            }
            
            // Validar stock
            if (maxStock === 0) {
                alert('Producto sin stock disponible');
                return;
            }
            
            if (quantity > maxStock) {
                alert(`Stock insuficiente. Solo hay ${maxStock} unidades disponibles.`);
                return;
            }

            const formData = new FormData();
            formData.append('producto_id', productoId);
            formData.append('variante_id', variantId);
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
                    const modalElement = document.getElementById('quick_view');
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    }
                    
                    alert('Producto agregado al carrito');
                    location.reload();
                } else {
                    alert(data.message || 'Error al agregar al carrito');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al agregar al carrito');
            });
        }

    })();