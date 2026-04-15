/**
 * Checkout functionality
 * Maneja la validación y envío del formulario de checkout
 */

(function($) {
    'use strict';

    // Ejecutar cuando el DOM esté listo
    $(document).ready(function() {
        
        // Validación del formulario de checkout
        const checkoutForm = $('#checkout-form');
        
        if (checkoutForm.length) {
            
            // Manejar el envío del formulario
            checkoutForm.on('submit', function(e) {
                const termsCheckbox = $('#check-agree');
                const provinceSelect = $('#province');
                const citySelect = $('#city');
                
                // ⚠️ IMPORTANTE: Habilitar el campo city ANTES de validar/enviar
                // Esto asegura que se incluya en el POST del formulario
                if (citySelect.prop('disabled')) {
                    citySelect.prop('disabled', false);
                }
                
                // Verificar que se aceptaron los términos
                if (!termsCheckbox.is(':checked')) {
                    e.preventDefault();
                    alert('Debes aceptar los términos y condiciones para continuar.');
                    return false;
                }
                
                // Validar campos requeridos (EXCEPTO los deshabilitados)
                let isValid = true;
                const requiredFields = checkoutForm.find('[required]');
                
                requiredFields.each(function() {
                    const field = $(this);
                    
                    // IMPORTANTE: No validar campos deshabilitados
                    if (field.prop('disabled')) {
                        field.removeClass('is-invalid');
                        return; // Continuar con el siguiente campo
                    }
                    
                    if (!field.val() || field.val().trim() === '' || field.val() === '---') {
                        isValid = false;
                        field.addClass('is-invalid');
                        
                        // Agregar mensaje de error si no existe
                        if (!field.next('.invalid-feedback').length) {
                            field.after('<div class="invalid-feedback">Este campo es requerido.</div>');
                        }
                    } else {
                        field.removeClass('is-invalid');
                        field.next('.invalid-feedback').remove();
                    }
                });
                
                // Validación adicional específica para provincia y ciudad
                if (!provinceSelect.val()) {
                    isValid = false;
                    provinceSelect.addClass('is-invalid');
                    if (!provinceSelect.next('.invalid-feedback').length) {
                        provinceSelect.after('<div class="invalid-feedback">Debes seleccionar una provincia.</div>');
                    }
                } else {
                    provinceSelect.removeClass('is-invalid');
                    provinceSelect.next('.invalid-feedback').remove();
                }
                
                if (!citySelect.val()) {
                    isValid = false;
                    citySelect.addClass('is-invalid');
                    if (!citySelect.next('.invalid-feedback').length) {
                        citySelect.after('<div class="invalid-feedback">Debes seleccionar una ciudad.</div>');
                    }
                } else {
                    citySelect.removeClass('is-invalid');
                    citySelect.next('.invalid-feedback').remove();
                }
                
                if (!isValid) {
                    e.preventDefault();
                    alert('Por favor, completa todos los campos requeridos.');
                    return false;
                }
                
                // Deshabilitar el botón de envío para evitar doble envío
                const submitBtn = $('#place-order-btn');
                submitBtn.prop('disabled', true);
                submitBtn.html('<span class="spinner-border spinner-border-sm me-2"></span>Procesando...');
                
                // Permitir que el formulario se envíe normalmente
                return true;
            });
            
            // Remover clase de error cuando el usuario escribe
            checkoutForm.find('[required]').on('input change', function() {
                const field = $(this);
                if (field.val() && field.val().trim() !== '' && field.val() !== '---') {
                    field.removeClass('is-invalid');
                    field.next('.invalid-feedback').remove();
                }
            });
            
            // Validación de email en tiempo real
            const emailField = $('#email');
            if (emailField.length) {
                emailField.on('blur', function() {
                    const email = $(this).val();
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    
                    if (email && !emailRegex.test(email)) {
                        $(this).addClass('is-invalid');
                        if (!$(this).next('.invalid-feedback').length) {
                            $(this).after('<div class="invalid-feedback">Por favor, ingresa un email válido.</div>');
                        }
                    } else {
                        $(this).removeClass('is-invalid');
                        $(this).next('.invalid-feedback').remove();
                    }
                });
            }
            
            // Validación de teléfono en tiempo real
            const phoneField = $('#phone');
            if (phoneField.length) {
                phoneField.on('blur', function() {
                    const phone = $(this).val();
                    // Solo números, espacios, guiones y paréntesis
                    const phoneRegex = /^[\d\s\-\(\)\+]+$/;
                    
                    if (phone && !phoneRegex.test(phone)) {
                        $(this).addClass('is-invalid');
                        if (!$(this).next('.invalid-feedback').length) {
                            $(this).after('<div class="invalid-feedback">Por favor, ingresa un teléfono válido.</div>');
                        }
                    } else {
                        $(this).removeClass('is-invalid');
                        $(this).next('.invalid-feedback').remove();
                    }
                });
            }
        }
        
        // Actualizar resumen de totales si se agrega/quita gift wrap
        // (esto debería estar integrado con el sistema de carrito existente)
        
        // Scroll suave al primer campo con error
        checkoutForm.on('submit', function() {
            setTimeout(function() {
                const firstError = $('.is-invalid').first();
                if (firstError.length) {
                    $('html, body').animate({
                        scrollTop: firstError.offset().top - 100
                    }, 500);
                }
            }, 100);
        });
    });

})(jQuery);
