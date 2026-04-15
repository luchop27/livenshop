// Sistema de Reseñas para Productos
(function() {
    'use strict';
    
    const productoSection = document.querySelector('[data-producto-id]');
    const productoId = productoSection ? productoSection.dataset.productoId : null;
    let currentSort = 'recent';
    
    // Agregar estilos CSS dinámicamente
    const style = document.createElement('style');
    style.textContent = `
        .rating-star {
            font-size: 30px;
            cursor: pointer;
            color: #ddd;
            transition: color 0.2s;
            display: inline-block;
            margin: 0 2px;
        }
        .rating-star:hover,
        .rating-star.active {
            color: #FFD700;
        }
        .rating-stars {
            font-size: 14px;
            letter-spacing: 2px;
        }
        .avatar-placeholder {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #007bff;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: bold;
        }
        .write-review-wrap {
            display: none;
        }
        .btn-cancel-review {
            display: none;
        }
    `;
    document.head.appendChild(style);
    
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
    
    // Cargar reseñas al iniciar
    document.addEventListener('DOMContentLoaded', function() {
        if (productoId) {
            loadReviews();
            setupEventListeners();
        }
    });
    
    function setupEventListeners() {
        // Botón Write a review
        const btnWriteReview = document.querySelector('.btn-write-review');
        const btnCancelReview = document.querySelector('.btn-cancel-review');
        const writeReviewWrap = document.querySelector('.write-review-wrap');
        
        if (btnWriteReview) {
            btnWriteReview.addEventListener('click', function() {
                writeReviewWrap.style.display = 'block';
                btnWriteReview.style.display = 'none';
                btnCancelReview.style.display = 'inline-block';
            });
        }
        
        if (btnCancelReview) {
            btnCancelReview.addEventListener('click', function() {
                writeReviewWrap.style.display = 'none';
                btnWriteReview.style.display = 'inline-block';
                btnCancelReview.style.display = 'none';
                document.getElementById('reviewForm').reset();
                document.getElementById('reviewRating').value = '0';
                document.querySelectorAll('.rating-star').forEach(star => {
                    star.classList.remove('active');
                });
            });
        }
        
        // Sistema de estrellas para rating
        const ratingStars = document.querySelectorAll('.rating-star');
        ratingStars.forEach(star => {
            star.addEventListener('click', function() {
                const rating = this.dataset.rating;
                document.getElementById('reviewRating').value = rating;
                
                // Actualizar visualización de estrellas
                ratingStars.forEach(s => {
                    if (parseInt(s.dataset.rating) >= parseInt(rating)) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
            });
        });
        
        // Submit del formulario de reseña
        const reviewForm = document.getElementById('reviewForm');
        if (reviewForm) {
            reviewForm.addEventListener('submit', function(e) {
                e.preventDefault();
                submitReview();
            });
        }
        
        // Ordenamiento de reseñas
        const sortSelect = document.getElementById('reviewSortBy');
        if (sortSelect) {
            sortSelect.addEventListener('change', function() {
                currentSort = this.value;
                loadReviews();
            });
        }
    }
    
    function loadReviews() {
        fetch(`/reviews/get/${productoId}/?sort=${currentSort}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateReviewsDisplay(data);
                }
            })
            .catch(error => {
                console.error('Error loading reviews:', error);
            });
    }
    
    function updateReviewsDisplay(data) {
        const { reviews, stats, user_has_reviewed } = data;
        
        // Actualizar promedio rating
        const avgElement = document.getElementById('averageRating');
        if (avgElement) {
            avgElement.textContent = stats.average > 0 ? stats.average.toFixed(1) : '0.0';
        }
        
        // Actualizar estrellas del promedio
        updateAverageStars(stats.average);
        
        // Actualizar total de ratings
        const totalText = document.getElementById('totalRatingsText');
        if (totalText) {
            totalText.textContent = `(${stats.total} Rating${stats.total !== 1 ? 's' : ''})`;
        }
        
        document.getElementById('totalReviewsCount').textContent = stats.total;
        
        // Actualizar barras de rating
        const totalReviews = stats.total || 1;
        [5, 4, 3, 2, 1].forEach(rating => {
            const count = stats.rating_counts[rating] || 0;
            const percentage = stats.total > 0 ? (count / stats.total) * 100 : 0;
            const item = document.querySelector(`.rating-score .item[data-rating="${rating}"]`);
            if (item) {
                const bar = item.querySelector('.rating-bar');
                const countEl = item.querySelector('.rating-count');
                if (bar) bar.style.width = `${percentage}%`;
                if (countEl) countEl.textContent = count;
            }
        });
        
        // Mostrar/ocultar formulario según si el usuario ya reseñó
        const userStatusDiv = document.getElementById('userReviewStatus');
        const reviewForm = document.getElementById('reviewForm');
        
        if (user_has_reviewed && userStatusDiv && reviewForm) {
            userStatusDiv.classList.remove('d-none');
            userStatusDiv.classList.add('alert-info');
            userStatusDiv.innerHTML = '<p class="mb-0">You have already reviewed this product. You can see your review below.</p>';
            reviewForm.style.display = 'none';
            
            // Ocultar botones de write review
            const btnWrite = document.querySelector('.btn-write-review');
            const btnCancel = document.querySelector('.btn-cancel-review');
            if (btnWrite) btnWrite.style.display = 'none';
            if (btnCancel) btnCancel.style.display = 'none';
        } else if (userStatusDiv) {
            userStatusDiv.classList.add('d-none');
        }
        
        // Actualizar lista de reseñas
        const container = document.getElementById('reviewsContainer');
        if (reviews.length === 0) {
            container.innerHTML = '<p class="text-center text_black-2 py-5">No reviews yet. Be the first to review this product!</p>';
        } else {
            container.innerHTML = reviews.map(review => createReviewHTML(review)).join('');
        }
    }
    
    function updateAverageStars(average) {
        const starsContainer = document.getElementById('averageStars');
        if (!starsContainer) return;
        
        const stars = starsContainer.querySelectorAll('i');
        const fullStars = Math.floor(average);
        
        stars.forEach((star, index) => {
            if (index < fullStars) {
                star.style.color = '#FFD700';
            } else {
                star.style.color = '#ddd';
            }
        });
    }
    
    function createReviewHTML(review) {
        const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
        
        let html = `
            <div class="reply-comment-item">
                <div class="user">
                    <div class="image">
                        <div class="avatar-placeholder">${review.user_name.charAt(0).toUpperCase()}</div>
                    </div>
                    <div>
                        ${review.title ? `<h6><span class="link">${review.title}</span></h6>` : ''}
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="rating-stars text-warning">${stars}</span>
                            ${review.verified ? '<span class="badge bg-success text-white" style="font-size: 10px;">Verified Purchase</span>' : ''}
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <span class="fw-6">${review.user_name}</span>
                            <span class="day text_black-2">${review.created_at}</span>
                        </div>
                    </div>
                </div>
                <p class="text_black-2">${review.comment}</p>
            </div>
        `;
        
        // Agregar respuestas si existen
        if (review.replies && review.replies.length > 0) {
            review.replies.forEach(reply => {
                html += `
                    <div class="reply-comment-item type-reply">
                        <div class="user">
                            <div class="image">
                                <div class="avatar-placeholder">M</div>
                            </div>
                            <div>
                                <h6>
                                    <span class="link">Reply from ${reply.user_name}</span>
                                </h6>
                                <div class="day text_black-2">${reply.created_at}</div>
                            </div>
                        </div>
                        <p class="text_black-2">${reply.comment}</p>
                    </div>
                `;
            });
        }
        
        return html;
    }
    
    function submitReview() {
        const rating = document.getElementById('reviewRating').value;
        const title = document.getElementById('reviewTitle').value;
        const comment = document.getElementById('reviewComment').value;
        
        if (!rating || rating === '0') {
            alert('Please select a rating');
            return;
        }
        
        if (!comment.trim()) {
            alert('Please write a comment');
            return;
        }
        
        const formData = new FormData();
        formData.append('rating', rating);
        formData.append('title', title);
        formData.append('comment', comment);
        
        fetch(`/reviews/submit/${productoId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Review submitted successfully!');
                // Resetear formulario
                document.getElementById('reviewForm').reset();
                document.getElementById('reviewRating').value = '0';
                document.querySelectorAll('.rating-star').forEach(star => {
                    star.classList.remove('active');
                });
                
                // Ocultar formulario
                document.querySelector('.write-review-wrap').style.display = 'none';
                document.querySelector('.btn-write-review').style.display = 'inline-block';
                document.querySelector('.btn-cancel-review').style.display = 'none';
                
                // Recargar reseñas
                loadReviews();
            } else {
                alert(data.message || 'Error submitting review');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error submitting review');
        });
    }
    
})();
