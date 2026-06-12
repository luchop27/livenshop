from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # ── PANEL ADMIN ───────────────────────────────────
    path('panel-admin/categorias/', views.panel_admin_categories, name='panel_admin_categories'),
    path('panel-admin/categorias/nueva/', views.panel_admin_category_add, name='panel_admin_category_add'),
    path('panel-admin/categorias/<int:categoria_id>/editar/', views.panel_admin_category_edit, name='panel_admin_category_edit'),
    path('panel-admin/categorias/<int:categoria_id>/eliminar/', views.panel_admin_category_delete, name='panel_admin_category_delete'),
    path('panel-admin/marcas/', views.panel_admin_brands, name='panel_admin_brands'),
    path('panel-admin/marcas/nueva/', views.panel_admin_brand_add, name='panel_admin_brand_add'),
    path('panel-admin/marcas/<int:brand_id>/editar/', views.panel_admin_brand_edit, name='panel_admin_brand_edit'),
    path('panel-admin/marcas/<int:brand_id>/eliminar/', views.panel_admin_brand_delete, name='panel_admin_brand_delete'),
    path('panel-admin/colecciones/', views.panel_admin_collections, name='panel_admin_collections'),
    path('panel-admin/colecciones/nueva/', views.panel_admin_collection_add, name='panel_admin_collection_add'),
    path('panel-admin/colecciones/<int:coleccion_id>/editar/', views.panel_admin_collection_edit, name='panel_admin_collection_edit'),
    path('panel-admin/colecciones/<int:coleccion_id>/eliminar/', views.panel_admin_collection_delete, name='panel_admin_collection_delete'),
    path('panel-admin/productos/', views.panel_admin_products, name='panel_admin_products'),
    path('panel-admin/productos/nuevo/', views.panel_admin_product_add, name='panel_admin_product_add'),
    path('panel-admin/productos/<int:producto_id>/editar/', views.panel_admin_product_edit, name='panel_admin_product_edit'),
    path('panel-admin/productos/<int:producto_id>/eliminar/', views.panel_admin_product_delete, name='panel_admin_product_delete'),
    path('panel/shopgram/', views.panel_admin_shopgram_list, name='panel_admin_shopgram_list'),
    path('panel/shopgram/add/', views.panel_admin_shopgram_add, name='panel_admin_shopgram_add'),
    path('panel/shopgram/<int:pk>/edit/', views.panel_admin_shopgram_edit, name='panel_admin_shopgram_edit'),
    path('panel/shopgram/<int:pk>/delete/', views.panel_admin_shopgram_delete, name='panel_admin_shopgram_delete'),

    # ── PANEL ADMIN - PEDIDOS ─────────────────────────
    path('panel-admin/pedidos/', views.panel_admin_orders, name='panel_admin_orders'),
    path('panel-admin/pedidos/<int:pedido_id>/', views.panel_admin_order_detail, name='panel_admin_order_detail'),
    path('panel-admin/pedidos/<int:pedido_id>/estado/', views.panel_admin_order_update_status, name='panel_admin_order_update_status'),

    # ── CATÁLOGO ──────────────────────────────────────
    path('shop/', views.ProductoListView.as_view(), name='lista_productos'),
    path('producto/<slug:slug>/', views.ProductoDetailView.as_view(), name='detalle_producto'),
    path('categoria/<slug:slug>/', views.CategoriaListView.as_view(), name='lista_por_categoria'),
    path('coleccion/<slug:slug>/', views.ColeccionListView.as_view(), name='lista_por_coleccion'),
    path('marcas/<slug:slug>/', views.MarcaListView.as_view(), name='lista_por_marca'),
     path('marca/<slug:slug>/', views.productos_por_marca, name='productos_por_marca'),  # ← NUEVA RUTA

    # ── CARRITO & CHECKOUT ───────────────────────────────────────
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/add-gift/', views.cart_add_gift, name='cart_add_gift'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.checkout_process, name='checkout_process'),
    path('checkout/payment/<int:pedido_id>/', views.order_payment_payphone, name='order_payment_payphone'),
    path('pagos/payphone/respuesta/', views.payphone_respuesta, name='payphone_respuesta'),
    path('pagos/payphone/cancelado/', views.payphone_cancelado, name='payphone_cancelado'),
    path('checkout/confirmation/<int:pedido_id>/', views.order_confirmation, name='order_confirmation'),
    path('checkout/validate-discount/', views.validate_discount_code, name='validate_discount_code'),

    # ── API ────────────────────────────────────────────
    path('api/producto/<int:producto_id>/quick-view/', views.producto_quick_view, name='producto_quick_view'),

    # ── WISHLIST ───────────────────────────────────────
    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/toggle/', views.wishlist_toggle, name='wishlist_toggle'),
]
