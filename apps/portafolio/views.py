from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json

from .models import Proyecto, ItemLookbook, Servicio
from apps.productos.models import Producto, Categoria, Marca


# ══════════════════════════════════════════════════════
# SERVICIOS PÚBLICO
# ══════════════════════════════════════════════════════

def servicios_publico(request):
    servicios = Servicio.objects.filter(activo=True).order_by('posicion')
    return render(request, 'services.html', {'servicios': servicios})


# ══════════════════════════════════════════════════════
# PANEL ADMIN — SERVICIOS
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_servicios_list(request):
    servicios = Servicio.objects.order_by('posicion')
    return render(request, 'panel_admin/servicios_list.html', {'servicios': servicios})


@staff_member_required(login_url='usuarios:login')
def panel_servicio_add(request):
    if request.method == 'POST':
        servicio = _guardar_servicio(request, None)
        if servicio:
            messages.success(request, f'Servicio "{servicio.titulo}" creado exitosamente.')
            return redirect('portafolio:servicios_list')
    return render(request, 'panel_admin/servicio_form.html', {'accion': 'Nuevo'})


@staff_member_required(login_url='usuarios:login')
def panel_servicio_edit(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    if request.method == 'POST':
        servicio = _guardar_servicio(request, servicio)
        if servicio:
            messages.success(request, f'Servicio "{servicio.titulo}" actualizado.')
            return redirect('portafolio:servicios_list')
    return render(request, 'panel_admin/servicio_form.html', {
        'accion': 'Editar',
        'servicio': servicio,
    })


@staff_member_required(login_url='usuarios:login')
def panel_servicio_delete(request, servicio_id):
    servicio = get_object_or_404(Servicio, pk=servicio_id)
    nombre = servicio.titulo
    servicio.delete()
    messages.success(request, f'Servicio "{nombre}" eliminado.')
    return redirect('portafolio:servicios_list')


def _guardar_servicio(request, servicio):
    titulo = request.POST.get('titulo', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()
    lado_imagen = request.POST.get('lado_imagen', 'izquierda')
    posicion = request.POST.get('posicion', '0').strip()
    activo = request.POST.get('activo') == 'on'

    if not titulo:
        messages.error(request, 'El título es obligatorio.')
        return None

    try:
        posicion = int(posicion)
    except ValueError:
        posicion = 0

    if servicio is None:
        servicio = Servicio()

    servicio.titulo = titulo
    servicio.descripcion = descripcion
    servicio.lado_imagen = lado_imagen
    servicio.posicion = posicion
    servicio.activo = activo

    imagen = request.FILES.get('imagen')
    if imagen:
        servicio.imagen = imagen
    elif request.POST.get('borrar_imagen') == '1' and servicio.imagen:
        servicio.imagen = None

    servicio.save()
    return servicio


# ══════════════════════════════════════════════════════
# PORTAFOLIO PÚBLICO
# ══════════════════════════════════════════════════════

def portafolio_publico(request):
    """
    Vista pública del portafolio.
    Muestra todos los proyectos activos con sus pines y productos asociados.
    """
    proyectos = Proyecto.objects.filter(
        activo=True
    ).prefetch_related('items__producto__imagenes').order_by('posicion', 'created_at')

    return render(request, 'portafolio.html', {
        'proyectos': proyectos,
    })


# ══════════════════════════════════════════════════════
# PANEL ADMIN — PORTAFOLIO
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_portafolio_list(request):
    """
    Listado de proyectos para el panel administrativo.
    """
    proyectos = Proyecto.objects.prefetch_related('items').order_by('posicion', 'created_at')

    return render(request, 'panel_admin/portafolio_list.html', {
        'proyectos': proyectos,
    })


@staff_member_required(login_url='usuarios:login')
def panel_portafolio_add(request):
    """
    Formulario para crear un nuevo proyecto de portafolio.
    Redirige al editor de pines tras guardar.
    """
    if request.method == 'POST':
        proyecto = _guardar_proyecto(request, None)
        if proyecto:
            messages.success(request, f'Proyecto "{proyecto.titulo}" creado exitosamente.')
            return redirect('portafolio:edit', proyecto_id=proyecto.pk)

    productos = Producto.objects.filter(activo=True).select_related('marca').prefetch_related('imagenes')

    return render(request, 'panel_admin/portafolio_add.html', {
        'productos': productos,
    })


@staff_member_required(login_url='usuarios:login')
def panel_portafolio_edit(request, proyecto_id):
    """
    Formulario para editar un proyecto existente.
    Incluye editor visual de pines.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)

    if request.method == 'POST':
        proyecto = _guardar_proyecto(request, proyecto)
        if proyecto:
            messages.success(request, f'Proyecto "{proyecto.titulo}" actualizado exitosamente.')
            return redirect('portafolio:edit', proyecto_id=proyecto.pk)

    productos = Producto.objects.filter(activo=True).select_related('marca').prefetch_related('imagenes')
    categorias = Categoria.objects.filter(activo=True, padre__isnull=True).prefetch_related('subcategorias').order_by('posicion', 'nombre')
    marcas = Marca.objects.filter(activo=True).order_by('nombre')

    return render(request, 'panel_admin/portafolio_edit.html', {
        'proyecto': proyecto,
        'productos': productos,
        'categorias': categorias,
        'marcas': marcas,
    })


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_portafolio_delete(request, proyecto_id):
    """
    Elimina un proyecto. Solo acepta POST.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    titulo = proyecto.titulo
    proyecto.delete()
    messages.success(request, f'Proyecto "{titulo}" eliminado correctamente.')
    return redirect('portafolio:list')


# ══════════════════════════════════════════════════════
# APIs — PINES DEL EDITOR VISUAL
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
@require_POST
def guardar_items(request, proyecto_id):
    """
    Guarda los pines del editor visual (llamado por AJAX).
    Reemplaza todos los items existentes del proyecto.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)

    try:
        data = json.loads(request.body)
        items = data.get('items', [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Reemplaza todos los items del proyecto
    proyecto.items.all().delete()

    for i, item in enumerate(items):
        producto_id = item.get('producto_id')
        producto = None
        if producto_id:
            try:
                producto = Producto.objects.get(pk=producto_id)
            except Producto.DoesNotExist:
                pass

        ItemLookbook.objects.create(
            proyecto=proyecto,
            producto=producto,
            pos_x=float(item.get('pos_x', 50)),
            pos_y=float(item.get('pos_y', 50)),
            posicion=i,
        )

    return JsonResponse({'ok': True, 'total': len(items)})


@staff_member_required(login_url='usuarios:login')
def items_json(request, proyecto_id):
    """
    Retorna los items de un proyecto en JSON para el editor visual.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)

    items = []
    for item in proyecto.items.select_related('producto').prefetch_related('producto__imagenes'):
        imagen_producto = ''
        if item.producto:
            primera_img = item.producto.imagenes.first()
            if primera_img:
                imagen_producto = primera_img.src

        items.append({
            'id':               item.pk,
            'producto_id':      item.producto.pk    if item.producto else None,
            'producto_nombre':  item.producto.nombre if item.producto else '',
            'producto_precio':  str(item.producto.precio) if item.producto else '',
            'producto_imagen':  imagen_producto,
            'pos_x':            float(item.pos_x),
            'pos_y':            float(item.pos_y),
        })

    return JsonResponse({'items': items})


# ══════════════════════════════════════════════════════
# HELPER PRIVADO
# ══════════════════════════════════════════════════════

def _guardar_proyecto(request, proyecto):
    """
    Crea o actualiza un proyecto con los datos del POST.
    Retorna el proyecto guardado o None si hay errores.
    """
    titulo = request.POST.get('titulo', '').strip()

    if not titulo:
        messages.error(request, 'El título del proyecto es obligatorio.')
        return None

    if proyecto is None:
        proyecto = Proyecto()

    proyecto.titulo      = titulo
    proyecto.subtitulo   = request.POST.get('subtitulo', '').strip()
    proyecto.descripcion = request.POST.get('descripcion', '').strip()
    proyecto.etiqueta    = request.POST.get('etiqueta', '').strip()
    proyecto.lado_imagen = request.POST.get('lado_imagen', 'izquierda')
    proyecto.posicion    = int(request.POST.get('posicion', 0) or 0)
    proyecto.activo      = request.POST.get('activo') == 'on'

    nueva_imagen = request.FILES.get('imagen')
    if nueva_imagen:
        proyecto.imagen = nueva_imagen

    proyecto.save()
    return proyecto