from django.contrib import admin
from .models import Plan, SeccionPlan

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