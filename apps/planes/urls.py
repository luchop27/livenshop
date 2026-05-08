from django.urls import path
from . import views

app_name = 'planes'

urlpatterns = [
    # ── PANEL ADMIN ───────────────────────────────────
    path('panel-admin/planes/', views.panel_admin_planes, name='panel_admin_planes'),
    path('panel-admin/planes/nuevo/', views.panel_admin_plan_add, name='panel_admin_plan_add'),
    path('panel-admin/planes/<int:plan_id>/editar/', views.panel_admin_plan_edit, name='panel_admin_plan_edit'),
    path('panel-admin/planes/<int:plan_id>/eliminar/', views.panel_admin_plan_delete, name='panel_admin_plan_delete'),

    # ── PÚBLICO ───────────────────────────────────────
    path('planes/<str:tipo>/', views.plan_detalle, name='detalle'),
]