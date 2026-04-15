/**
 * Script para manejar la funcionalidad del wishlist
 * Permite agregar/remover productos del wishlist del usuario
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('📌 Script de Wishlist cargado');
    
    // Obtener todos los botones del wishlist
    const wishlistButtons = document.querySelectorAll('.wishlist.btn-icon-action');
    
    if (wishlistButtons.length === 0) {
        console.log('⚠️ No se encontraron botones de wishlist');
        return;
    }
    
    console.log(`✅ Se encontraron ${wishlistButtons.length} botones de wishlist`);
    
    wishlistButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.getAttribute('data-product-id');
            const wishlistId = this.getAttribute('data-wishlist-id');
            
            console.log('🖱️ Click en wishlist:', {productId, wishlistId});
            
            if (!productId) {
                console.error('❌ No se encontró product-id');
                return;
            }
            
            if (wishlistId) {
                // El producto está en wishlist, removerlo
                removeFromWishlist(productId, wishlistId, this);
            } else {
                // El producto no está en wishlist, agregarlo
                addToWishlist(productId, this);
            }
        });
    });
    
    /**
     * Agregar producto al wishlist
     */
    function addToWishlist(productId, button) {
        console.log('➕ Agregando producto ' + productId + ' al wishlist');
        
        fetch('/api/wishlist/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'product_id=' + productId
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('✅ Producto agregado al wishlist');
                
                // Actualizar el botón
                button.classList.add('active');
                button.setAttribute('data-wishlist-id', data.wishlist_id);
                button.querySelector('.tooltip').textContent = 'Remove from Wishlist';
                
                // NO mostrar notificación
                
                // Contar items en wishlist
                updateWishlistCount();
            } else {
                console.error('❌ Error:', data.message);
                // NO mostrar notificación de error
            }
        })
        .catch(error => {
            console.error('❌ Error de red:', error);
            // NO mostrar notificación de error
        });
    }
    
    /**
     * Remover producto del wishlist
     */
    function removeFromWishlist(productId, wishlistId, button) {
        console.log('➖ Removiendo producto ' + productId + ' del wishlist');
        
        fetch('/api/wishlist/remove/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'wishlist_id=' + wishlistId
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('✅ Producto removido del wishlist');
                
                // Actualizar el botón
                button.classList.remove('active');
                button.removeAttribute('data-wishlist-id');
                button.querySelector('.tooltip').textContent = 'Add to Wishlist';
                
                // Si estamos en la página de wishlist, remover el producto de la lista
                const isWishlistPage = window.location.pathname.includes('/wishlist');
                if (isWishlistPage) {
                    const productCard = button.closest('.card-product');
                    if (productCard) {
                        productCard.style.transition = 'opacity 0.3s ease';
                        productCard.style.opacity = '0';
                        setTimeout(() => {
                            productCard.remove();
                            
                            // Verificar si quedan productos
                            const remainingProducts = document.querySelectorAll('.card-product').length;
                            if (remainingProducts === 0) {
                                // Recargar la página para mostrar el mensaje de "lista vacía"
                                window.location.reload();
                            }
                        }, 300);
                    }
                }
                
                // NO mostrar notificación
                
                // Contar items en wishlist
                updateWishlistCount();
            } else {
                console.error('❌ Error:', data.message);
                // NO mostrar notificación de error
            }
        })
        .catch(error => {
            console.error('❌ Error de red:', error);
            // NO mostrar notificación de error
        });
    }
    
    /**
     * Mostrar notificación
     */
    function showNotification(message, type) {
        console.log('🔔 Notificación:', message);
        
        // Crear elemento de notificación
        const notificacion = document.createElement('div');
        notificacion.className = `alert alert-${type} alert-dismissible fade show`;
        notificacion.style.position = 'fixed';
        notificacion.style.top = '20px';
        notificacion.style.right = '20px';
        notificacion.style.zIndex = '9999';
        notificacion.style.minWidth = '300px';
        notificacion.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notificacion);
        
        // Auto remover después de 3 segundos
        setTimeout(() => {
            notificacion.remove();
        }, 3000);
    }
    
    /**
     * Actualizar contador de wishlist
     */
    function updateWishlistCount() {
        fetch('/api/wishlist/count/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Buscar todos los enlaces de wishlist en el navbar
                    const wishlistLinks = document.querySelectorAll('.nav-wishlist a');
                    
                    wishlistLinks.forEach(link => {
                        // Buscar o crear el contador
                        let counter = link.querySelector('.count-box');
                        
                        if (data.count > 0) {
                            // Si hay items, mostrar/actualizar contador
                            if (!counter) {
                                // Crear el contador si no existe
                                counter = document.createElement('span');
                                counter.className = 'count-box';
                                link.appendChild(counter);
                            }
                            counter.textContent = data.count;
                            counter.style.display = 'flex'; // Asegurar que sea visible
                        } else {
                            // Si no hay items, ocultar contador
                            if (counter) {
                                counter.style.display = 'none';
                            }
                        }
                    });
                    
                    console.log('📌 Wishlist count actualizado:', data.count);
                }
            })
            .catch(error => {
                console.error('Error al actualizar contador:', error);
            });
    }
    
    /**
     * Obtener valor de cookie CSRF
     */
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
});
