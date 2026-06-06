from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, SeccionPlan, AliadoBeneficio, PlanNovios, MovimientoPlan, SolicitudPlanNovios


class SeccionPlanInline(admin.StackedInline):
    model = SeccionPlan
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo']
    list_editable = ['activo']
    inlines = [SeccionPlanInline]


@admin.register(SeccionPlan)
class SeccionPlanAdmin(admin.ModelAdmin):
    list_display = ['plan', 'titulo', 'orden']
    list_filter = ['plan']
    ordering = ['plan', 'orden']


@admin.register(AliadoBeneficio)
class AliadoBeneficioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'email', 'telefono', 'activo', 'orden']
    list_editable = ['activo', 'orden']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'descripcion_beneficio']


class MovimientoPlanInline(admin.TabularInline):
    model = MovimientoPlan
    extra = 0
    readonly_fields = ['fecha']


@admin.register(PlanNovios)
class PlanNoviosAdmin(admin.ModelAdmin):
    list_display = ['nombres', 'email', 'saldo_acumulado', 'fecha_boda', 'activo']
    list_editable = ['activo']
    search_fields = ['nombres', 'email']


@admin.register(SolicitudPlanNovios)
class SolicitudPlanNoviosAdmin(admin.ModelAdmin):
    list_display = ['foto_miniatura', 'nombres_novios', 'email', 'telefono', 'fecha_boda', 'estado', 'procesado', 'fecha_solicitud']
    list_filter = ['estado', 'procesado', 'fecha_solicitud']
    list_editable = ['estado', 'procesado']
    search_fields = ['nombres_novios', 'email', 'telefono']
    filter_horizontal = ['productos_regalo']
    inlines = [MovimientoPlanInline]

    def foto_miniatura(self, obj):
        if obj.foto_pareja:
            return format_html('<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />', obj.foto_pareja.url)
        return "Sin Foto"
    foto_miniatura.short_description = 'Foto'