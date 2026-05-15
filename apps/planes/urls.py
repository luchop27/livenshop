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

    # ── PANEL ADMIN — SOLICITUDES ─────────────────────────
    path('panel-admin/solicitudes-novios/', views.panel_admin_solicitudes, name='panel_admin_solicitudes'),
    path('panel-admin/solicitudes-novios/buscar-productos/', views.buscar_productos_admin, name='buscar_productos_admin'),
    path('panel-admin/solicitudes-novios/<int:solicitud_id>/estado/', views.panel_admin_solicitud_cambiar_estado, name='panel_admin_solicitud_estado'),
    path('panel-admin/solicitudes-novios/<int:solicitud_id>/editar/', views.panel_admin_solicitud_editar, name='panel_admin_solicitud_editar'),

    # ── PÚBLICO ────────────────────────────────────────────
    path('plan-novios/', views.plan_novios, name='plan_novios'),
    path('plan-novios/registro/', views.registro_novios, name='registro_novios'),
    path('beneficios/', views.beneficios_novios, name='beneficios'),
    path('portal-novios/', views.portal_novios, name='portal_novios'),

    # ── DEJAR REGALOS ─────────────────────────────────────
    path('dejar-regalos/matrimonios/', views.dejar_regalos_matrimonios, name='dejar_regalos_matrimonios'),
    path('dejar-regalos/matrimonios/<int:id>/', views.detalle_regalo_matrimonio, name='detalle_regalo_matrimonio'),
    path('dejar-regalos/cumpleanos/', views.dejar_regalos_cumpleanos, name='dejar_regalos_cumpleanos'),
    path('dejar-regalos/otros/', views.dejar_regalos_otros, name='dejar_regalos_otros'),

    # Ruta genérica (otros planes)
    path('planes/<str:tipo>/', views.plan_detalle, name='detalle'),
]