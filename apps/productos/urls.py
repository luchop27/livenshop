from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # ── CATÁLOGO ──────────────────────────────────────
    path('', views.ProductoListView.as_view(), name='lista_productos'),
    path('producto/<slug:slug>/', views.ProductoDetailView.as_view(), name='detalle_producto'),
    path('categoria/<slug:slug>/', views.CategoriaListView.as_view(), name='lista_por_categoria'),
    path('coleccion/<slug:slug>/', views.ColeccionListView.as_view(), name='lista_por_coleccion'),

    # ── CARRITO ───────────────────────────────────────
    path('carrito/', views.CarritoView.as_view(), name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/actualizar/', views.actualizar_cantidad, name='actualizar_cantidad'),

    # ── API ────────────────────────────────────────────

    path('api/producto/<int:producto_id>/quick-view/', views.producto_quick_view, name='producto_quick_view'),
]
