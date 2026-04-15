// static/js/product-detail.js
// Funcionalidad para la página de detalle del producto

(function () {
    'use strict';

    // Objeto para almacenar el stock de cada variante
    let variantesStock = {};
    let selectedVariant = null;
    let maxStock = 999; // Stock máximo por defecto

    // Inicializar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function () {
        // Pequeño delay para asegurar que main.js termine de ejecutarse
        setTimeout(function () {
            initializeVariantsStock();
            setupVariantSelectors();
            setupQuantityControls();
            updateStockInfo();
        }, 100);
    });

    // Inicializar el stock de las variantes desde los atributos data
    function initializeVariantsStock() {
        const variantElements = document.querySelectorAll('.variant-data');
        variantElements.forEach(function (element) {
            const variantId = element.dataset.variantId;
            const stock = parseInt(element.dataset.variantStock) || 0;
            const talla = element.dataset.variantSize || '';
            const color = element.dataset.variantColor || '';

            const key = `${color}_${talla}`.toLowerCase();
            variantesStock[key] = {
                id: variantId,
                stock: stock,
                talla: talla,
                color: color
            };
        });

        console.log('Variantes cargadas:', variantesStock);
    }

    // Configurar los selectores de variantes (color y talla)
    function setupVariantSelectors() {
        // Selectores de color
        const colorInputs = document.querySelectorAll('input[name="color1"]');
        colorInputs.forEach(function (input) {
            input.addEventListener('change', function () {
                updateSelectedVariant();
                updateStockInfo();
            });
        });

        // Selectores de talla
        const sizeInputs = document.querySelectorAll('input[name="size1"]');
        sizeInputs.forEach(function (input) {
            input.addEventListener('change', function () {
                updateSelectedVariant();
                updateStockInfo();
            });
        });
    }

    // Actualizar la variante seleccionada
    function updateSelectedVariant() {
        const selectedColor = document.querySelector('input[name="color1"]:checked');
        const selectedSize = document.querySelector('input[name="size1"]:checked');

        let color = '';
        let talla = '';

        if (selectedColor) {
            const colorLabel = document.querySelector(`label[for="${selectedColor.id}"]`);
            color = colorLabel ? colorLabel.dataset.value || '' : '';
        }

        if (selectedSize) {
            const sizeLabel = document.querySelector(`label[for="${selectedSize.id}"]`);
            talla = sizeLabel ? sizeLabel.dataset.value || '' : '';
        }

        const key = `${color}_${talla}`.toLowerCase();
        selectedVariant = variantesStock[key] || null;

        // Actualizar el stock máximo
        if (selectedVariant) {
            maxStock = selectedVariant.stock;
        } else {
            maxStock = 999;
        }

        // Ajustar la cantidad actual si excede el nuevo máximo
        const quantityInput = document.querySelector('.quantity-product');
        if (quantityInput) {
            const currentQty = parseInt(quantityInput.value) || 1;
            if (currentQty > maxStock) {
                quantityInput.value = maxStock;
                updateTotalPrice();
            }
        }
    }

    // Configurar los controles de cantidad
    function setupQuantityControls() {
        const decreaseBtn = document.querySelector('.btn-decrease');
        const increaseBtn = document.querySelector('.btn-increase');
        const quantityInput = document.querySelector('.quantity-product');

        // Remover todos los listeners previos clonando los elementos
        if (decreaseBtn) {
            const newDecreaseBtn = decreaseBtn.cloneNode(true);
            decreaseBtn.parentNode.replaceChild(newDecreaseBtn, decreaseBtn);

            newDecreaseBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (quantityInput) {
                    let value = parseInt(quantityInput.value) || 1;
                    if (value > 1) {
                        quantityInput.value = value - 1;
                        updateTotalPrice();
                    }
                }
            });
        }

        if (increaseBtn) {
            const newIncreaseBtn = increaseBtn.cloneNode(true);
            increaseBtn.parentNode.replaceChild(newIncreaseBtn, increaseBtn);

            newIncreaseBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (quantityInput) {
                    let value = parseInt(quantityInput.value) || 1;
                    // Solo incrementar si no excede el stock disponible
                    if (value < maxStock) {
                        quantityInput.value = value + 1;
                        updateTotalPrice();
                    } else {
                        // Mostrar mensaje de stock limitado
                        showStockLimitMessage();
                    }
                }
            });
        }

        // Validar entrada manual en el input
        if (quantityInput) {
            quantityInput.addEventListener('change', function () {
                let value = parseInt(this.value) || 1;
                if (value < 1) {
                    this.value = 1;
                } else if (value > maxStock) {
                    this.value = maxStock;
                    showStockLimitMessage();
                }
                updateTotalPrice();
            });

            quantityInput.addEventListener('keypress', function (e) {
                // Solo permitir números
                if (e.which < 48 || e.which > 57) {
                    e.preventDefault();
                }
            });
        }
    }

    // Actualizar información de stock en la página
    function updateStockInfo() {
        const stockInfoElement = document.getElementById('stock-info');
        if (stockInfoElement && selectedVariant) {
            if (selectedVariant.stock > 0) {
                if (selectedVariant.stock <= 5) {
                    stockInfoElement.innerHTML = `<span class="text-warning"><i class="icon-warning"></i> Only ${selectedVariant.stock} left in stock!</span>`;
                } else {
                    stockInfoElement.innerHTML = `<span class="text-success"><i class="icon-check"></i> In stock (${selectedVariant.stock} available)</span>`;
                }
            } else {
                stockInfoElement.innerHTML = `<span class="text-danger"><i class="icon-close"></i> Out of stock</span>`;
                // Deshabilitar botón de agregar al carrito
                const addToCartBtn = document.querySelector('.btn-add-to-cart');
                if (addToCartBtn) {
                    addToCartBtn.classList.add('disabled');
                    addToCartBtn.style.opacity = '0.5';
                    addToCartBtn.style.pointerEvents = 'none';
                }
            }
        }
    }

    // Actualizar el precio total
    function updateTotalPrice() {
        const quantityInput = document.querySelector('.quantity-product');
        const priceElement = document.querySelector('.tf-product-info-price .price, .tf-product-info-price .price-on-sale');
        const totalPriceElement = document.querySelector('.tf-qty-price');

        if (quantityInput && priceElement && totalPriceElement) {
            const quantity = parseInt(quantityInput.value) || 1;
            const priceText = priceElement.textContent.replace('$', '').trim();
            const price = parseFloat(priceText);

            if (!isNaN(price)) {
                const total = (price * quantity).toFixed(2);
                totalPriceElement.textContent = `$${total}`;
            }
        }
    }

    // Mostrar mensaje cuando se alcanza el límite de stock
    function showStockLimitMessage() {
        const stockInfoElement = document.getElementById('stock-info');
        if (stockInfoElement && selectedVariant) {
            const originalHTML = stockInfoElement.innerHTML;
            stockInfoElement.innerHTML = `<span class="text-danger"><i class="icon-warning"></i> Maximum quantity available: ${maxStock}</span>`;

            // Restaurar el mensaje original después de 3 segundos
            setTimeout(function () {
                updateStockInfo();
            }, 3000);
        } else {
            // Si no hay elemento de stock info, mostrar alert
            alert(`Maximum quantity available: ${maxStock}`);
        }
    }

    // Exponer funciones globalmente si es necesario
    window.productDetail = {
        getSelectedVariant: function () {
            return selectedVariant;
        },
        getMaxStock: function () {
            return maxStock;
        },
        updateStockInfo: updateStockInfo
    };

})();
