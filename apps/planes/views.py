from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Plan, SeccionPlan, AliadoBeneficio, PlanNovios, MovimientoPlan, SolicitudPlanNovios
import hashlib


# ── PÚBLICO ───────────────────────────────────────────────────────────────────

def plan_detalle(request, tipo):
    """Vista genérica de detalle de un plan. Redirige novios a la landing premium."""
    if tipo == 'novios':
        return plan_novios(request)
    plan = get_object_or_404(Plan, tipo=tipo, activo=True)
    return render(request, f'planes/plan_{tipo}.html', {'plan': plan})


def plan_novios(request):
    """Landing premium del Plan de Novios."""
    plan = Plan.objects.filter(tipo='novios', activo=True).first()

    try:
        aliados = AliadoBeneficio.objects.filter(activo=True).order_by('orden', 'nombre')
        aliados = list(aliados)
    except Exception:
        aliados = []

    return render(request, 'planes/plan_novios.html', {
        'plan': plan,
        'aliados': aliados,
    })


def registro_novios(request):
    """Página dedicada al formulario de registro del Plan de Novios."""
    if request.method == 'POST':
        try:
            SolicitudPlanNovios.objects.create(
                nombres_novios=request.POST.get('nombres_novios'),
                email=request.POST.get('email'),
                telefono=request.POST.get('telefono'),
                fecha_boda=request.POST.get('fecha_boda'),
                ciudad=request.POST.get('ciudad', ''),
                mensaje=request.POST.get('mensaje', '')
            )
            messages.success(request, '¡Gracias! Tu solicitud ha sido enviada. Nos contactaremos contigo muy pronto.')
            # No redireccionamos para que el mensaje se vea en el mismo contexto
        except Exception:
            messages.error(request, 'Ocurrió un error al enviar tu solicitud. Por favor verifica los datos.')
    
    return render(request, 'planes/registro_novios.html')



def beneficios_novios(request):
    """Galería de aliados / beneficios del Plan de Novios."""
    categoria = request.GET.get('cat', '')
    try:
        aliados = AliadoBeneficio.objects.filter(activo=True)
        if categoria:
            aliados = aliados.filter(categoria=categoria)
        aliados = list(aliados.order_by('orden', 'nombre'))
    except Exception:
        aliados = []
    categorias = AliadoBeneficio.CATEGORIA_CHOICES
    return render(request, 'planes/beneficios_novios.html', {
        'aliados': aliados,
        'categorias': categorias,
        'categoria_activa': categoria,
    })


def portal_novios(request):
    """Portal de acceso 24/7 para novios registrados."""
    plan_data = None
    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        clave = request.POST.get('clave', '').strip()
        clave_hash = hashlib.sha256(clave.encode()).hexdigest()

        try:
            registro = PlanNovios.objects.get(email=email, activo=True)
            if registro.clave == clave_hash:
                plan_data = registro
            else:
                error = 'Clave incorrecta. Por favor verifica tus datos.'
        except PlanNovios.DoesNotExist:
            error = 'No encontramos un plan registrado con ese email.'

    return render(request, 'planes/portal_novios.html', {
        'plan_data': plan_data,
        'error': error,
    })


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


# ── PANEL ADMIN — ALIADOS ─────────────────────────────────────────────────────

@staff_member_required(login_url='usuarios:login')
def panel_admin_aliados(request):
    aliados = AliadoBeneficio.objects.all().order_by('orden', 'nombre')
    return render(request, 'panel_admin/planes/lista_aliados.html', {'aliados': aliados})


@staff_member_required(login_url='usuarios:login')
def panel_admin_aliado_add(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            aliado = AliadoBeneficio(
                nombre=nombre,
                categoria=request.POST.get('categoria', 'otro'),
                descripcion_beneficio=request.POST.get('descripcion_beneficio', ''),
                email=request.POST.get('email', '') or None,
                telefono=request.POST.get('telefono', '') or None,
                instagram=request.POST.get('instagram', '') or None,
                sitio_web=request.POST.get('sitio_web', '') or None,
                activo=request.POST.get('activo') == 'on',
                orden=int(request.POST.get('orden', 0)),
            )
            if 'logo' in request.FILES:
                aliado.logo = request.FILES['logo']
            aliado.save()
            messages.success(request, f'Aliado "{nombre}" creado correctamente.')
            return redirect('planes:panel_admin_aliados')
    return render(request, 'panel_admin/planes/aliado_form.html', {
        'categorias': AliadoBeneficio.CATEGORIA_CHOICES,
        'accion': 'Nuevo',
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_aliado_edit(request, aliado_id):
    aliado = get_object_or_404(AliadoBeneficio, pk=aliado_id)
    if request.method == 'POST':
        aliado.nombre = request.POST.get('nombre', aliado.nombre).strip()
        aliado.categoria = request.POST.get('categoria', aliado.categoria)
        aliado.descripcion_beneficio = request.POST.get('descripcion_beneficio', '')
        aliado.email = request.POST.get('email', '') or None
        aliado.telefono = request.POST.get('telefono', '') or None
        aliado.instagram = request.POST.get('instagram', '') or None
        aliado.sitio_web = request.POST.get('sitio_web', '') or None
        aliado.activo = request.POST.get('activo') == 'on'
        aliado.orden = int(request.POST.get('orden', 0))
        if 'logo' in request.FILES:
            aliado.logo = request.FILES['logo']
        aliado.save()
        messages.success(request, f'Aliado "{aliado.nombre}" actualizado.')
        return redirect('planes:panel_admin_aliados')
    return render(request, 'panel_admin/planes/aliado_form.html', {
        'aliado': aliado,
        'categorias': AliadoBeneficio.CATEGORIA_CHOICES,
        'accion': 'Editar',
    })


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_aliado_delete(request, aliado_id):
    aliado = get_object_or_404(AliadoBeneficio, pk=aliado_id)
    nombre = aliado.nombre
    aliado.delete()
    messages.success(request, f'Aliado "{nombre}" eliminado.')
    return redirect('planes:panel_admin_aliados')