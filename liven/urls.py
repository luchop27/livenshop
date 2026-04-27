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

urlpatterns = [
    path('admin/', admin.site.urls),



    # Home y panel van después
    path('', home, name='home'),
    path('panel-admin/', panel_admin_demo, name='panel_admin_demo'),
    # ← Includes PRIMERO para que Django resuelva rutas específicas antes
    path('', include('apps.productos.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('about/', TemplateView.as_view(template_name='about-us.html'), name='about'),
    path('portfolio/', TemplateView.as_view(template_name='portfolio.html'), name='portfolio'),
    path('brands/', TemplateView.as_view(template_name='brands.html'), name='brands'),
    path('shop/', TemplateView.as_view(template_name='shop-fullwidth.html'), name='shop'),
    path('services/', TemplateView.as_view(template_name='services.html'), name='services'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('login/', usuarios_views.login_usuario, name='login'),
    path('logout/', usuarios_views.logout_usuario, name='logout'),
    path('register/', usuarios_views.registrar_usuario, name='register'),
    path('my-account/', usuarios_views.my_account, name='my-account'),
    path('wishlist/', TemplateView.as_view(template_name='my-account-wishlist.html'), name='wishlist'),
    path('my-account/orders/', usuarios_views.my_account_orders, name='my-account-orders'),
    path('my-account/orders/<int:order_id>/', TemplateView.as_view(template_name='my-account-orders-details.html'), name='my-account-orders-details'),
    path('my-account/edit/', usuarios_views.my_account_edit, name='my-account-edit'),
    path('my-account/address/', usuarios_views.my_account_address, name='my-account-address'),
    path('my-account/wishlist/', TemplateView.as_view(template_name='my-account-wishlist.html'), name='my-account-wishlist'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)