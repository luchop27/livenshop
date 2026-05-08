from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Plan, SeccionPlan


# ── PÚBLICO ───────────────────────────────────────────────────────────────────

def plan_detalle(request, tipo):
    plan = get_object_or_404(Plan, tipo=tipo, activo=True)
    return render(request, f'planes/plan_{tipo}.html', {'plan': plan})


# ── PANEL ADMIN ───────────────────────────────────────────────────────────────

@staff_member_required(login_url='usuarios:login')
def panel_admin_planes(request):
    planes = Plan.objects.all().order_by('tipo')
    return render(request, 'panel_admin/planes/lista_planes.html', {'planes': planes})


@staff_member_required(login_url='usuarios:login')
def panel_admin_plan_add(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        nombre = request.POST.get('nombre')
        activo = request.POST.get('activo') == 'True'
        titulo_terminos = request.POST.get('titulo_terminos', 'Términos')
        contenido_terminos = request.POST.get('contenido_terminos', '')
        titulo_beneficios = request.POST.get('titulo_beneficios', 'Beneficios')
        contenido_beneficios = request.POST.get('contenido_beneficios', '')
        texto_boton_principal = request.POST.get('texto_boton_principal', '')
        url_boton_principal = request.POST.get('url_boton_principal', '')
        texto_boton_secundario = request.POST.get('texto_boton_secundario', '')
        url_boton_secundario = request.POST.get('url_boton_secundario', '')

        if not tipo or not nombre:
            messages.error(request, 'El tipo y nombre son obligatorios.')
        elif Plan.objects.filter(tipo=tipo).exists():
            messages.error(request, f'Ya existe un plan con el tipo "{tipo}".')
        else:
            Plan.objects.create(
                tipo=tipo,
                nombre=nombre,
                activo=activo,
                titulo_terminos=titulo_terminos,
                contenido_terminos=contenido_terminos,
                titulo_beneficios=titulo_beneficios,
                contenido_beneficios=contenido_beneficios,
                texto_boton_principal=texto_boton_principal,
                url_boton_principal=url_boton_principal,
                texto_boton_secundario=texto_boton_secundario,
                url_boton_secundario=url_boton_secundario,
            )
            messages.success(request, f'Plan "{nombre}" creado correctamente.')
            return redirect('planes:panel_admin_planes')

    return render(request, 'panel_admin/planes/nuevo_plan.html', {
        'tipo_choices': Plan.TIPO_CHOICES,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_plan_edit(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)

    if request.method == 'POST':
        plan.nombre = request.POST.get('nombre', plan.nombre)
        plan.activo = request.POST.get('activo') == 'True'
        plan.titulo_terminos = request.POST.get('titulo_terminos', plan.titulo_terminos)
        plan.contenido_terminos = request.POST.get('contenido_terminos', plan.contenido_terminos)
        plan.titulo_beneficios = request.POST.get('titulo_beneficios', plan.titulo_beneficios)
        plan.contenido_beneficios = request.POST.get('contenido_beneficios', plan.contenido_beneficios)
        plan.texto_boton_principal = request.POST.get('texto_boton_principal', '')
        plan.url_boton_principal = request.POST.get('url_boton_principal', '')
        plan.texto_boton_secundario = request.POST.get('texto_boton_secundario', '')
        plan.url_boton_secundario = request.POST.get('url_boton_secundario', '')
        plan.save()
        messages.success(request, f'Plan "{plan.nombre}" actualizado correctamente.')
        return redirect('planes:panel_admin_planes')

    return render(request, 'panel_admin/planes/editar_plan.html', {'plan': plan})


@staff_member_required(login_url='usuarios:login')
def panel_admin_plan_delete(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    if request.method == 'POST':
        nombre = plan.nombre
        plan.delete()
        messages.success(request, f'Plan "{nombre}" eliminado.')
    return redirect('planes:panel_admin_planes')