from django.urls import path
from . import views

app_name = 'planes'

urlpatterns = [
    # ── PANEL ADMIN — PLANES ───────────────────────────────
    path('panel-admin/planes/', views.panel_admin_planes, name='panel_admin_planes'),
    path('panel-admin/planes/nuevo/', views.panel_admin_plan_add, name='panel_admin_plan_add'),
    path('panel-admin/planes/<int:plan_id>/editar/', views.panel_admin_plan_edit, name='panel_admin_plan_edit'),
    path('panel-admin/planes/<int:plan_id>/eliminar/', views.panel_admin_plan_delete, name='panel_admin_plan_delete'),

    # ── PANEL ADMIN — ALIADOS ──────────────────────────────
    path('panel-admin/aliados/', views.panel_admin_aliados, name='panel_admin_aliados'),
    path('panel-admin/aliados/nuevo/', views.panel_admin_aliado_add, name='panel_admin_aliado_add'),
    path('panel-admin/aliados/<int:aliado_id>/editar/', views.panel_admin_aliado_edit, name='panel_admin_aliado_edit'),
    path('panel-admin/aliados/<int:aliado_id>/eliminar/', views.panel_admin_aliado_delete, name='panel_admin_aliado_delete'),

    # ── PÚBLICO ────────────────────────────────────────────
    path('plan-novios/', views.plan_novios, name='plan_novios'),
    path('plan-novios/registro/', views.registro_novios, name='registro_novios'),
    path('beneficios/', views.beneficios_novios, name='beneficios'),
    path('portal-novios/', views.portal_novios, name='portal_novios'),

    # Ruta genérica (otros planes)
    path('planes/<str:tipo>/', views.plan_detalle, name='detalle'),
]