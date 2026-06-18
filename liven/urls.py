"""
URL configuration for liven project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from apps.productos.views import home, panel_admin_demo
from apps.usuarios import views as usuarios_views
from apps.portafolio import views as portafolio_views

urlpatterns = [
    path('admin/', admin.site.urls),



    # Home y panel van después
    path('', home, name='home'),
    path('panel-admin/', panel_admin_demo, name='panel_admin_demo'),
    # ← Includes PRIMERO para que Django resuelva rutas específicas antes
    path('', include('apps.planes.urls')),
    path('', include('apps.portafolio.urls', namespace='portafolio')),
    path('', include(('apps.productos.urls', 'productos'))),
    path('usuarios/', include('apps.usuarios.urls')),
    path('about/', TemplateView.as_view(template_name='about-us.html'), name='about'),
    path('categorias/', TemplateView.as_view(template_name='shop-fullwidth.html'), name='categorias'),
    path('services/', portafolio_views.servicios_publico, name='services'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('iniciar-sesion/', usuarios_views.login_usuario, name='login'),
    path('cerrar-sesion/', usuarios_views.logout_usuario, name='logout'),
    path('registro/', usuarios_views.registrar_usuario, name='register'),
    path('my-account/', usuarios_views.my_account, name='my-account'),
    path('wishlist/', usuarios_views.my_account_wishlist, name='wishlist'),
    path('my-account/orders/', usuarios_views.my_account_orders, name='my-account-orders'),
    path('my-account/orders/<int:pedido_id>/', usuarios_views.my_account_orders_details, name='my-account-orders-details'),
    path('my-account/edit/', usuarios_views.my_account_edit, name='my-account-edit'),
    path('my-account/address/', usuarios_views.my_account_address, name='my-account-address'),
    path('my-account/wishlist/', usuarios_views.my_account_wishlist, name='my-account-wishlist'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)