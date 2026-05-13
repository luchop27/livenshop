from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.http import JsonResponse
from .models import Plan, SeccionPlan, AliadoBeneficio, PlanNovios, MovimientoPlan, SolicitudPlanNovios
import hashlib
import urllib.parse


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
        nombres = request.POST.get('nombres_novios', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        fecha_boda = request.POST.get('fecha_boda', '')
        ciudad = request.POST.get('ciudad', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()

        if not nombres or not email or not telefono or not fecha_boda:
            messages.error(request, 'Por favor completa todos los campos requeridos.')
        else:
            try:
                SolicitudPlanNovios.objects.create(
                    nombres_novios=nombres,
                    email=email,
                    telefono=telefono,
                    fecha_boda=fecha_boda,
                    ciudad=ciudad,
                    mensaje=mensaje,
                )
                # Notificación WhatsApp al administrador
                wa_msg = (
                    f"💍 *Nueva Solicitud Plan de Novios*%0a%0a"
                    f"*Novios:* {urllib.parse.quote(nombres)}%0a"
                    f"*Email:* {urllib.parse.quote(email)}%0a"
                    f"*Teléfono:* {urllib.parse.quote(telefono)}%0a"
                    f"*Fecha boda:* {fecha_boda}%0a"
                    f"*Ciudad:* {urllib.parse.quote(ciudad or 'No especificada')}%0a"
                    f"*Mensaje:* {urllib.parse.quote(mensaje or 'Ninguno')}%0a%0a"
                    f"Revisa el panel admin para aprobar el plan."
                )
                wa_url = f"https://wa.me/593989387657?text={wa_msg}"
                messages.success(
                    request,
                    '¡Gracias! Tu solicitud ha sido enviada. Nos contactaremos contigo muy pronto.'
                )
                # Guardamos URL de WA en sesión para mostrar botón en la confirmación
                request.session['wa_admin_url'] = wa_url
            except Exception as e:
                messages.error(request, 'Ocurrió un error al enviar tu solicitud. Por favor verifica los datos.')

    wa_url = request.session.pop('wa_admin_url', None)
    return render(request, 'planes/registro_novios.html', {'wa_url': wa_url})


# ── PÚBLICO — DEJAR REGALOS ──────────────────────────────────────────────────

def dejar_regalos_matrimonios(request):
    """Lista pública de bodas aprobadas donde los invitados pueden dejar regalos."""
    q = request.GET.get('q', '').strip()
    solicitudes = SolicitudPlanNovios.objects.filter(estado='aprobado')
    if q:
        solicitudes = solicitudes.filter(
            Q(nombres_novios__icontains=q) | Q(ciudad__icontains=q)
        )
    solicitudes = solicitudes.order_by('fecha_boda')
    return render(request, 'planes/dejar_regalos_matrimonios.html', {
        'solicitudes': solicitudes,
        'query': q,
    })

def detalle_regalo_matrimonio(request, id):
    """Página de detalle para dejar un regalo a una pareja específica."""
    solicitud = get_object_or_404(SolicitudPlanNovios, pk=id, estado='aprobado')
    return render(request, 'planes/detalle_regalo_matrimonio.html', {
        's': solicitud,
    })


def dejar_regalos_cumpleanos(request):
    """Sección de cumpleaños — próximamente."""
    return render(request, 'planes/dejar_regalos_cumpleanos.html')


def dejar_regalos_otros(request):
    """Sección de otros eventos — próximamente."""
    return render(request, 'planes/dejar_regalos_otros.html')



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
            registro = SolicitudPlanNovios.objects.get(email=email, estado='aprobado')
            if registro.clave and (registro.clave == clave_hash or registro.clave == clave):
                plan_data = registro
            elif not registro.clave:
                error = 'Tu plan está aprobado pero aún no se te ha asignado una clave. Contacta a Liven.'
            else:
                error = 'Clave incorrecta. Por favor verifica tus datos.'
        except SolicitudPlanNovios.DoesNotExist:
            error = 'No encontramos un plan aprobado con ese email.'

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
def panel_admin_solicitudes(request):
    """Lista de solicitudes del Plan de Novios con filtro por estado."""
    estado = request.GET.get('estado', '')
    solicitudes = SolicitudPlanNovios.objects.all()
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    return render(request, 'panel_admin/planes/lista_solicitudes.html', {
        'solicitudes': solicitudes,
        'estado_choices': SolicitudPlanNovios.ESTADO_CHOICES,
        'estado_activo': estado,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_solicitud_cambiar_estado(request, solicitud_id):
    """Cambia el estado de una solicitud (GET simple para rapidez)."""
    solicitud = get_object_or_404(SolicitudPlanNovios, pk=solicitud_id)
    nuevo_estado = request.GET.get('estado', 'pendiente')
    if nuevo_estado in ['pendiente', 'aprobado', 'finalizado']:
        solicitud.estado = nuevo_estado
        solicitud.save(update_fields=['estado'])
        messages.success(request, f'Estado actualizado a "{solicitud.get_estado_display()}".')
    return redirect('planes:panel_admin_solicitudes')


@staff_member_required(login_url='usuarios:login')
def panel_admin_solicitud_editar(request, solicitud_id):
    """Vista personalizada para editar una solicitud y añadirle productos de regalo fácilmente."""
    from .forms import SolicitudPlanNoviosForm
    solicitud = get_object_or_404(SolicitudPlanNovios, pk=solicitud_id)
    
    if request.method == 'POST':
        form = SolicitudPlanNoviosForm(request.POST, instance=solicitud)
        if form.is_valid():
            form.save()
            messages.success(request, f'La solicitud de {solicitud.nombres_novios} ha sido actualizada con éxito.')
            return redirect('planes:panel_admin_solicitudes')
        else:
            messages.error(request, 'Error al guardar. Por favor, revisa los campos.')
    else:
        form = SolicitudPlanNoviosForm(instance=solicitud)
        
    return render(request, 'panel_admin/planes/editar_solicitud.html', {
        'form': form,
        'solicitud': solicitud,
    })


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