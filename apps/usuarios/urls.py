from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticación
    path('iniciar-sesion/', views.login_usuario, name='login'),
    path('registro/', views.registrar_usuario, name='register'),
    path('cerrar-sesion/', views.logout_usuario, name='logout'),
    
    # API para ciudades por provincia (AJAX)
    path('api/ciudades-por-provincia/<int:provincia_id>/', views.api_ciudades_por_provincia, name='api_ciudades_por_provincia'),
    
    # Recuperación de contraseña con CÓDIGO DE 6 DÍGITOS
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    path('password-reset/resend/', views.password_reset_resend, name='password_reset_resend'),
    
    # Verificación de email
    path('verificar-email/<uuid:token>/', views.verificar_email, name='verificar_email'),
    path('reenviar-verificacion/', views.reenviar_verificacion, name='reenviar_verificacion'),
    
    # Panel de usuario (rutas principales en español)
    path('mi-cuenta/', views.my_account, name='my_account'),
    path('mi-cuenta/pedidos/', views.my_account_orders, name='my_account_orders'),
    path('mi-cuenta/pedidos/<int:pedido_id>/', views.my_account_orders_details, name='my_account_orders_details'),
    path('mi-cuenta/direcciones/', views.my_account_address, name='my_account_address'),
    path('mi-cuenta/detalles/', views.my_account_edit, name='my_account_edit'),
    path('mi-cuenta/favoritos/', views.my_account_wishlist, name='my_account_wishlist'),

    # Compatibilidad con rutas antiguas en inglés
    path('my-account/', views.my_account),
    path('my-account/orders/', views.my_account_orders),
    path('my-account/orders/<int:pedido_id>/', views.my_account_orders_details),
    path('my-account/address/', views.my_account_address),
    path('my-account/edit/', views.my_account_edit),
    path('my-account/wishlist/', views.my_account_wishlist),
    
    # Wishlist AJAX (rutas principales en español)
    path('favoritos/agregar/<int:producto_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('favoritos/eliminar/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('favoritos/verificar/<int:producto_id>/', views.is_in_wishlist, name='is_in_wishlist'),

    # Compatibilidad con rutas antiguas en inglés
    path('wishlist/add/<int:producto_id>/', views.add_to_wishlist),
    path('wishlist/remove/<int:wishlist_id>/', views.remove_from_wishlist),
    path('wishlist/check/<int:producto_id>/', views.is_in_wishlist),

    # Panel Admin — Usuarios
    path('panel-admin/usuarios/', views.panel_admin_users, name='panel_admin_users'),
    path('panel-admin/usuarios/<int:usuario_id>/toggle-status/', views.panel_admin_user_toggle_status, name='panel_admin_user_toggle_status'),
]
