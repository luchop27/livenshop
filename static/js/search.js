// Sistema de Busqueda de Productos
(function($) {
    'use strict';

    // Variables globales
    let allProducts = [];
    let filteredProducts = [];
    let currentSearchQuery = '';

    $(document).ready(function() {
        console.log('Search.js: Script cargado');
        
        // Inicializar busqueda
        initializeSearch();
    });

    function initializeSearch() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        
        if (!searchInput) return;

        // Event listener para input
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim().toLowerCase();
            currentSearchQuery = query;

            if (query.length < 2) {
                if (searchResults) {
                    searchResults.innerHTML = '';
                }
                return;
            }

            performSearch(query);
        });

        // Event listener para Enter
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    window.location.href = '/buscar/?q=' + encodeURIComponent(query);
                }
            }
        });
    }

    function performSearch(query) {
        const searchResults = document.getElementById('search-results');
        
        if (!searchResults) return;

        // Buscar en el DOM o hacer fetch
        fetch('/api/search/?q=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(data => {
                displayResults(data.results);
            })
            .catch(error => {
                console.error('Error en busqueda:', error);
                searchResults.innerHTML = '<div class="alert alert-danger">Error en la busqueda</div>';
            });
    }

    function displayResults(results) {
        const searchResults = document.getElementById('search-results');
        
        if (!searchResults) return;

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="alert alert-info">No se encontraron resultados</div>';
            return;
        }

        let html = '<div class="search-results-list">';
        results.forEach(result => {
            html += `
                <a href="${result.url}" class="search-result-item">
                    <img src="${result.image}" alt="${result.name}" class="search-result-image">
                    <div class="search-result-info">
                        <h5>${result.name}</h5>
                        <p>$${result.price}</p>
                    </div>
                </a>
            `;
        });
        html += '</div>';

        searchResults.innerHTML = html;
    }

})(jQuery);











































































































})(jQuery);        });        initSearch();    $(document).ready(function() {        }        location.reload();        // Reload the default content when search is cleared    function loadDefaultProducts() {        }        $container.html(html);                });            html += '</div>';            html += '  </div>';            html += '    </div>';            }                html += '      <div class="price fw-6">' + product.precio + '</div>';            } else {                html += '      <div class="price-on-sale fw-6">' + product.precio + '</div>';                html += '      <div class="compare-at-price">' + product.precio_base + '</div>';            if (product.precio_base) {            html += '    <div class="tf-product-info-price">';            }                html += '    <div class="text-muted small">' + product.categoria + '</div>';            if (product.categoria) {            html += '    <a href="' + product.url + '">' + product.nombre + '</a>';            html += '  <div class="content">';            html += '  </div>';            html += '    </a>';            html += '      <img src="' + (product.imagen || '/static/images/products/white-1.jpg') + '" alt="' + product.nombre + '">';            html += '    <a href="' + product.url + '">';            html += '  <div class="image">';            html += '<div class="tf-loop-item">';        results.forEach(function(product) {                let html = '<div class="mb-3"><strong>Resultados para "' + query + '" (' + results.length + ')</strong></div>';        const $container = $('#search-results-container');    function displayResults(results, query) {        }        });            }                $container.html('<div class="text-center py-4 text-danger"><p>Error al buscar productos</p></div>');            error: function() {            },                }                    $container.html('<div class="text-center py-4"><p>No se encontraron resultados para "' + query + '"</p></div>');                } else {                    displayResults(response.results, query);                if (response.success && response.results.length > 0) {            success: function(response) {            data: { q: query },            method: 'GET',            url: '/api/search/',        $.ajax({                $container.html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');                const $container = $('#search-results-container');    function searchProducts(query) {        }        });            loadDefaultProducts();            $input.val('');        $('#canvasSearch').on('hidden.bs.offcanvas', function() {                });            }                searchProducts(query);            if (query.length >= 2) {            const query = $input.val().trim();            e.preventDefault();        $form.on('submit', function(e) {                });            }, 300);                searchProducts(query);            searchTimeout = setTimeout(function() {                        }                return;                loadDefaultProducts();            if (query.length < 2) {                        clearTimeout(searchTimeout);                        const query = $(this).val().trim();        $input.on('input', function() {                if (!$input.length) return;                const $container = $('#search-results-container');        const $input = $form.find('input[name="text"]');        const $form = $('.tf-mini-search-frm');    function initSearch() {        let searchTimeout = null;        'use strict';(function($) { */ * Sistema de búsqueda en tiempo real * SISTEMA DE BÚSQUEDA EN TIEMPO REAL
 * Búsqueda de productos AJAX con resultados dinámicos
 */

(function($) {
    'use strict';

    let searchTimeout = null;
    const MIN_SEARCH_LENGTH = 2;
    const SEARCH_DELAY = 300; // ms

    /**
     * Inicializar búsqueda en tiempo real
     */
    function initSearch() {
        const $searchForm = $('.tf-mini-search-frm');
        const $searchInput = $searchForm.find('input[name="text"]');
        const $searchResults = $('.tf-search-content');
        const $resultsContainer = $('.tf-col-content .tf-search-hidden-inner');
        const $quickLinks = $('.tf-col-quicklink');
        const $noResultsContainer = $('.tf-cart-hide-has-results');

        if ($searchInput.length === 0) {
            return;
        }

        // Evento de escritura en el input
        $searchInput.on('input', function() {
            const query = $(this).val().trim();

            // Limpiar timeout anterior
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            // Si la búsqueda es muy corta, mostrar contenido por defecto
            if (query.length < MIN_SEARCH_LENGTH) {
                showDefaultContent();
                return;
            }

            // Delay para evitar muchas peticiones
            searchTimeout = setTimeout(function() {
                performSearch(query);
            }, SEARCH_DELAY);
        });

        // Prevenir submit del formulario y ejecutar búsqueda
        $searchForm.on('submit', function(e) {
            e.preventDefault();
            const query = $searchInput.val().trim();
            if (query.length >= MIN_SEARCH_LENGTH) {
                performSearch(query);
            }
        });

        /**
         * Mostrar contenido por defecto (Quick Links e inspiración)
         */
        function showDefaultContent() {
            $noResultsContainer.show();
        }

        /**
         * Realizar búsqueda AJAX
         */
        function performSearch(query) {
            // Mostrar loading
            showLoading();

            $.ajax({
                url: '/api/search/',
                method: 'GET',
                data: { q: query },
                dataType: 'json',
                success: function(response) {
                    if (response.success && response.results.length > 0) {
                        displayResults(response.results, query);
                    } else {
                        showNoResults(query);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error en búsqueda:', error);
                    showError();
                }
            });
        }

        /**
         * Mostrar loading
         */
        function showLoading() {
            const loadingHTML = `
                <div class="search-loading text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Buscando...</span>
                    </div>
                    <p class="mt-2 text-muted">Buscando productos...</p>
                </div>
            `;
            $resultsContainer.html(loadingHTML);
            $noResultsContainer.show();
            $quickLinks.hide();
        }

        /**
         * Mostrar resultados de búsqueda
         */
        function displayResults(results, query) {
            let html = `
                <div class="search-results-header mb-3">
                    <div class="tf-search-content-title fw-5">
                        Resultados para "${query}" (${results.length})
                    </div>
                </div>
            `;

            results.forEach(function(product) {
                // Determinar precio a mostrar
                let priceHTML = '';
                if (product.precio_base) {
                    // Hay descuento
                    priceHTML = `
                        <div class="tf-product-info-price">
                            <div class="compare-at-price">${product.precio_base}</div>
                            <div class="price-on-sale fw-6">${product.precio}</div>
                        </div>
                    `;
                } else {
                    // Precio normal
                    priceHTML = `
                        <div class="tf-product-info-price">
                            <div class="price fw-6">${product.precio}</div>
                        </div>
                    `;
                }

                // Imagen por defecto si no hay
                const imageSrc = product.imagen || '/static/images/products/placeholder.jpg';

                html += `
                    <div class="tf-loop-item">
                        <div class="image">
                            <a href="${product.url}">
                                <img src="${imageSrc}" alt="${product.nombre}" onerror="this.src='/static/images/products/placeholder.jpg'">
                            </a>
                        </div>
                        <div class="content">
                            <a href="${product.url}">${product.nombre}</a>
                            ${product.categoria ? `<div class="text-muted small">${product.categoria}</div>` : ''}
                            ${priceHTML}
                        </div>
                    </div>
                `;
            });

            $resultsContainer.html(html);
            $noResultsContainer.show();
            $quickLinks.hide();
        }

        /**
         * Mostrar mensaje de "sin resultados"
         */
        function showNoResults(query) {
            const html = `
                <div class="search-no-results text-center py-4">
                    <i class="icon-search fs-1 text-muted mb-3"></i>
                    <p class="fw-5 mb-2">No se encontraron resultados para "${query}"</p>
                    <p class="text-muted">Intenta con otras palabras clave</p>
                </div>
            `;
            $resultsContainer.html(html);
            $noResultsContainer.show();
            $quickLinks.hide();
        }

        /**
         * Mostrar error
         */
        function showError() {
            const html = `
                <div class="search-error text-center py-4">
                    <i class="icon-close fs-1 text-danger mb-3"></i>
                    <p class="fw-5 mb-2">Error al buscar</p>
                    <p class="text-muted">Por favor, intenta de nuevo</p>
                </div>
            `;
            $resultsContainer.html(html);
            $noResultsContainer.show();
            $quickLinks.hide();
        }

        /**
         * Limpiar búsqueda al cerrar el canvas
         */
        $('#canvasSearch').on('hidden.bs.offcanvas', function () {
            $searchInput.val('');
            showDefaultContent();
        });
    }

    // Inicializar cuando el DOM esté listo
    $(document).ready(function() {
        initSearch();
    });

})(jQuery);
