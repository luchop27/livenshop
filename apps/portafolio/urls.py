from django.urls import path
from . import views

app_name = 'portafolio'

urlpatterns = [
    # ── PÚBLICO ───────────────────────────────────────────
    path('portafolio/', views.portafolio_publico, name='portafolio'),

    # ── PANEL ADMIN — PORTAFOLIO ──────────────────────────
    path('panel-admin/portafolio/', views.panel_portafolio_list, name='list'),
    path('panel-admin/portafolio/nuevo/', views.panel_portafolio_add, name='add'),
    path('panel-admin/portafolio/<int:proyecto_id>/editar/', views.panel_portafolio_edit, name='edit'),
    path('panel-admin/portafolio/<int:proyecto_id>/eliminar/', views.panel_portafolio_delete, name='delete'),

    # ── PANEL ADMIN — SERVICIOS ───────────────────────────
    path('panel-admin/servicios/', views.panel_servicios_list, name='servicios_list'),
    path('panel-admin/servicios/nuevo/', views.panel_servicio_add, name='servicio_add'),
    path('panel-admin/servicios/<int:servicio_id>/editar/', views.panel_servicio_edit, name='servicio_edit'),
    path('panel-admin/servicios/<int:servicio_id>/eliminar/', views.panel_servicio_delete, name='servicio_delete'),

    # ── API ────────────────────────────────────────────────
    path('panel-admin/portafolio/<int:proyecto_id>/items/guardar/', views.guardar_items, name='guardar_items'),
    path('panel-admin/portafolio/<int:proyecto_id>/items/json/', views.items_json, name='items_json'),
]