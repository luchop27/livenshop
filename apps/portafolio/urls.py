from django.urls import path
from . import views

app_name = 'portafolio'

urlpatterns = [
    # ── PÚBLICO ───────────────────────────────────────────
    path('portafolio/', views.portafolio_publico, name='portafolio'),

    # ── PANEL ADMIN ───────────────────────────────────────
    path('panel-admin/portafolio/', views.panel_portafolio_list, name='list'),
    path('panel-admin/portafolio/nuevo/', views.panel_portafolio_add, name='add'),
    path('panel-admin/portafolio/<int:proyecto_id>/editar/', views.panel_portafolio_edit, name='edit'),
    path('panel-admin/portafolio/<int:proyecto_id>/eliminar/', views.panel_portafolio_delete, name='delete'),

    # ── API ────────────────────────────────────────────────
    path('panel-admin/portafolio/<int:proyecto_id>/items/guardar/', views.guardar_items, name='guardar_items'),
    path('panel-admin/portafolio/<int:proyecto_id>/items/json/', views.items_json, name='items_json'),
]