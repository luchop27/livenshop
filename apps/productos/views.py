from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.contrib import messages
from django.conf import settings
from django.utils.text import slugify
from .models import Marca, Producto, Categoria, Coleccion, CarritoItem, Imagen, AtributoProducto, ShopGramPost, Pedido, PedidoItem
from .cart import Cart
from .services.payphone import preparar_pago_payphone, confirmar_pago_payphone
from decimal import Decimal


def _active_marcas():
    return Marca.objects.filter(activo=True).order_by('nombre')


# ══════════════════════════════════════════════════════
# HOME - FUNCTION BASED VIEW
# ══════════════════════════════════════════════════════

def home(request):

    productos = Producto.objects.filter(
        activo=True
    ).select_related('marca').prefetch_related('imagenes')[:12]

    categorias = Categoria.objects.filter(
        activo=True,
        padre=None
    ).order_by('posicion', 'nombre')[:6]

    colecciones = Coleccion.objects.filter(
        activo=True,
        destacada=True
    )

    marcas_slider = Marca.objects.filter(
        activo=True,
        mostrar_en_slider=True
    ).order_by('orden_slider', 'nombre')

    shop_gram_posts = ShopGramPost.objects.filter(
        activo=True
    )[:10]

    marcas = Marca.objects.filter(
        activo=True
    ).order_by('nombre')

    anuncios_bar = Coleccion.objects.filter(
        activo=True,
        es_promocion=True
    ).exclude(
        texto_anuncio__isnull=True
    ).exclude(
        texto_anuncio__exact=''
    )

    return render(request, 'home.html', {
        'productos': productos,
        'categorias': categorias,
        'colecciones': colecciones,
        'marcas_slider': marcas_slider,
        'shop_gram_posts': shop_gram_posts,
        'marcas': marcas,
        'tiene_slides': marcas_slider.exists() or colecciones.exists(),
        'anuncios_bar': anuncios_bar,
    })

def panel_admin_shopgram_list(request):
    search = request.GET.get('q', '').strip()
    posts = ShopGramPost.objects.all()
    if search:
        posts = posts.filter(instagram_url__icontains=search)
    return render(request, 'panel_admin/panel_admin_shopgram_list.html', {'posts': posts, 'search': search})

def panel_admin_shopgram_add(request):
    if request.method == 'POST':
        instagram_url = request.POST.get('instagram_url', '').strip()
        activo = request.POST.get('activo') == 'True'
        imagen = request.FILES.get('imagen')

        if not instagram_url:
            messages.error(request, 'La URL de Instagram es obligatoria.')
        else:
            post = ShopGramPost(instagram_url=instagram_url, activo=activo)
            if imagen:
                post.imagen = imagen
            post.save()
            messages.success(request, 'Publicación creada correctamente.')
            return redirect('productos:panel_admin_shopgram_list')

    return render(request, 'panel_admin/panel_admin_shopgram_add.html')

def panel_admin_shopgram_edit(request, pk):
    post = get_object_or_404(ShopGramPost, pk=pk)

    if request.method == 'POST':
        post.instagram_url = request.POST.get('instagram_url', '').strip()
        post.activo = request.POST.get('activo') == 'True'

        if request.POST.get('remove_imagen') == '1' and post.imagen:
            post.imagen.delete(save=False)
            post.imagen = None

        if request.FILES.get('imagen'):
            if post.imagen:
                post.imagen.delete(save=False)
            post.imagen = request.FILES['imagen']

        post.save()
        messages.success(request, 'Publicación actualizada correctamente.')
        return redirect('productos:panel_admin_shopgram_list')

    return render(request, 'panel_admin/panel_admin_shopgram_edit.html', {'post': post})

def panel_admin_shopgram_delete(request, pk):
    post = get_object_or_404(ShopGramPost, pk=pk)
    if request.method == 'POST':
        if post.imagen:
            post.imagen.delete(save=False)
        post.delete()
        messages.success(request, 'Publicación eliminada.')
    return redirect('productos:panel_admin_shopgram_list')

def productos_por_marca(request, slug):
    if slug == 'todos':
        productos = Producto.objects.filter(activo=True).prefetch_related('imagenes').select_related('marca')
    else:
        marca = get_object_or_404(Marca, slug=slug, activo=True)
        productos = Producto.objects.filter(marca=marca, activo=True).prefetch_related('imagenes')

    data = []
    for p in productos:
        imgs = list(p.imagenes.all())
        data.append({
            'id': p.id,
            'nombre': p.nombre,
            'url': p.get_absolute_url(),
            'precio': str(p.precio),
            'precio_oferta': str(p.precio_oferta) if p.precio_oferta else None,
            'tiene_oferta': p.tiene_oferta(),
            'porcentaje_descuento': p.porcentaje_descuento(),
            'imagen_1': imgs[0].src if len(imgs) > 0 else '',
            'imagen_2': imgs[1].src if len(imgs) > 1 else '',
        })

    return JsonResponse({'productos': data})

@staff_member_required(login_url='usuarios:login')
def panel_admin_dashboard(request):
    """
    Dashboard principal del panel administrativo.
    Muestra métricas globales de la tienda.
    """
    from apps.usuarios.models import Usuario
    total_productos = Producto.objects.count()
    total_activos = Producto.objects.filter(activo=True).count()
    total_categorias = Categoria.objects.count()
    total_colecciones = Coleccion.objects.count()
    total_usuarios = Usuario.objects.filter(is_active=True).count()

    # Productos más recientes
    productos_recientes = Producto.objects.select_related(
        'categoria', 'marca'
    ).prefetch_related('imagenes').order_by('-created_at')[:5]

    # Categorías con más productos
    top_categorias = Categoria.objects.annotate(
        num_productos=Count('productos', distinct=True)
    ).order_by('-num_productos')[:5]

    return render(request, 'panel_admin/dashboard.html', {
        'total_productos': total_productos,
        'total_activos': total_activos,
        'total_inactivos': total_productos - total_activos,
        'total_categorias': total_categorias,
        'total_colecciones': total_colecciones,
        'total_usuarios': total_usuarios,
        'productos_recientes': productos_recientes,
        'top_categorias': top_categorias,
    })


# Alias para compatibilidad con url existente en liven/urls.py
panel_admin_demo = panel_admin_dashboard


# ══════════════════════════════════════════════════════
# PANEL ADMIN — PRODUCTOS
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_admin_products(request):
    """
    Listado de productos para el panel administrativo.
    Incluye filtro por texto, coleccion y paginacion.
    """
    search = request.GET.get('q', '').strip()
    coleccion_filtro = request.GET.get('coleccion', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    productos_qs = Producto.objects.select_related(
        'categoria', 'coleccion', 'marca'
    ).prefetch_related('imagenes').order_by('-created_at')

    if search:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search) |
            Q(marca__nombre__icontains=search) |
            Q(slug__icontains=search)
        )

    if coleccion_filtro:
        productos_qs = productos_qs.filter(coleccion__slug=coleccion_filtro)

    if estado_filtro == 'activo':
        productos_qs = productos_qs.filter(activo=True)
    elif estado_filtro == 'inactivo':
        productos_qs = productos_qs.filter(activo=False)

    paginator = Paginator(productos_qs, 15)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    colecciones_disponibles = Coleccion.objects.filter(activo=True).order_by('nombre')

    return render(request, 'panel_admin/product_list.html', {
        'productos': productos,
        'total_productos': paginator.count,
        'search': search,
        'coleccion_filtro': coleccion_filtro,
        'estado_filtro': estado_filtro,
        'colecciones_disponibles': colecciones_disponibles,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_product_add(request):
    """
    Formulario para crear un nuevo producto decorativo.
    Sin variantes de talla/color — stock y precio directos.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        precio_oferta = request.POST.get('precio_oferta', '').strip() or None
        stock = request.POST.get('stock', '9999')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_completa = request.POST.get('descripcion_completa', '').strip()
        marca_id = request.POST.get('marca') or None
        sku = request.POST.get('sku', '').strip() or None
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
        capacidad = request.POST.get('capacidad', '').strip()
        peso = request.POST.get('peso') or None
        destacado = request.POST.get('destacado') == 'on'
        activo = request.POST.get('activo') == 'on'

        if not nombre:
            messages.error(request, 'El nombre del producto es obligatorio.')
        else:
            # Generar slug único
            base_slug = slugify(nombre)
            slug = base_slug
            counter = 1
            while Producto.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            producto = Producto.objects.create(
                nombre=nombre,
                slug=slug,
                sku=sku,
                precio=precio,
                precio_oferta=precio_oferta,
                stock=stock,
                categoria_id=categoria_id,
                coleccion_id=coleccion_id,
                marca_id=marca_id,
                descripcion_corta=descripcion_corta,
                descripcion_completa=descripcion_completa,
                material=material,
                dimensiones=dimensiones,
                capacidad=capacidad,
                peso=peso,
                destacado=destacado,
                activo=activo,
            )

            # Guardar imágenes subidas
            imagenes = request.FILES.getlist('imagenes')
            for i, img in enumerate(imagenes):
                Imagen.objects.create(
                    producto=producto,
                    imagen=img,
                    tipo_medio='imagen',
                    es_principal=(i == 0),
                    posicion=i,
                )

            messages.success(request, f'Producto "{nombre}" creado exitosamente.')
            return redirect('productos:panel_admin_products')

    categorias = Categoria.objects.filter(activo=True).order_by('padre__nombre', 'nombre')
    colecciones = Coleccion.objects.filter(activo=True).order_by('nombre')
    marcas = _active_marcas()

    return render(request, 'panel_admin/product_add.html', {
        'categorias': categorias,
        'colecciones': colecciones,
        'marcas': marcas,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_product_edit(request, producto_id):
    """
    Formulario para editar un producto existente.
    """
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        precio = request.POST.get('precio', '0')
        precio_oferta = request.POST.get('precio_oferta', '').strip() or None
        stock = request.POST.get('stock', '9999')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_completa = request.POST.get('descripcion_completa', '').strip()
        marca_id = request.POST.get('marca') or None
        sku = request.POST.get('sku', '').strip() or None
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
        capacidad = request.POST.get('capacidad', '').strip()
        peso = request.POST.get('peso') or None
        destacado = request.POST.get('destacado') == 'on'
        activo = request.POST.get('activo') == 'on'

        if not nombre:
            messages.error(request, 'El nombre del producto es obligatorio.')
        else:
            # Actualizar slug solo si el nombre cambió
            if nombre != producto.nombre:
                base_slug = slugify(nombre)
                slug = base_slug
                counter = 1
                while Producto.objects.filter(slug=slug).exclude(pk=producto.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                producto.slug = slug

            producto.nombre = nombre
            producto.sku = sku
            producto.precio = precio
            producto.precio_oferta = precio_oferta
            producto.stock = stock
            producto.categoria_id = categoria_id
            producto.coleccion_id = coleccion_id
            producto.marca_id = marca_id
            producto.descripcion_corta = descripcion_corta
            producto.descripcion_completa = descripcion_completa
            producto.material = material
            producto.dimensiones = dimensiones
            producto.capacidad = capacidad
            producto.peso = peso
            producto.destacado = destacado
            producto.activo = activo
            producto.save()

            # Añadir nuevas imágenes si se subieron
            imagenes_nuevas = request.FILES.getlist('imagenes')
            posicion_base = producto.imagenes.count()
            for i, img in enumerate(imagenes_nuevas):
                Imagen.objects.create(
                    producto=producto,
                    imagen=img,
                    tipo_medio='imagen',
                    es_principal=False,
                    posicion=posicion_base + i,
                )

            # Eliminar imágenes marcadas
            ids_eliminar = request.POST.getlist('eliminar_imagen')
            if ids_eliminar:
                Imagen.objects.filter(pk__in=ids_eliminar, producto=producto).delete()

            messages.success(request, f'Producto "{nombre}" actualizado exitosamente.')
            return redirect('productos:panel_admin_products')

    categorias = Categoria.objects.filter(activo=True).order_by('padre__nombre', 'nombre')
    colecciones = Coleccion.objects.filter(activo=True).order_by('nombre')
    marcas = _active_marcas()

    return render(request, 'panel_admin/product_edit.html', {
        'producto': producto,
        'categorias': categorias,
        'colecciones': colecciones,
        'marcas': marcas,
    })


# ══════════════════════════════════════════════════════
# PANEL ADMIN — MARCAS
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_admin_brands(request):
    search = request.GET.get('q', '').strip()
    marcas = Marca.objects.annotate(num_productos=Count('productos', distinct=True))

    if search:
        marcas = marcas.filter(nombre__icontains=search)

    marcas = marcas.order_by('nombre')

    return render(request, 'panel_admin/brand_list.html', {
        'marcas': marcas,
        'search': search,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_brand_add(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('estado', 'True') == 'True'
        imagen = request.FILES.get('imagen') or None
        mostrar_en_slider = request.POST.get('mostrar_en_slider') == 'on'
        orden_slider = int(request.POST.get('orden_slider', 0) or 0)
        imagen_slider = request.FILES.get('imagen_slider') or None
        imagen_slider_movil = request.FILES.get('imagen_slider_movil') or None


        if not nombre:
            messages.error(request, 'El nombre de la marca es obligatorio.')
        else:
            slug = slug_manual if slug_manual else slugify(nombre)
            base_slug = slug
            counter = 1
            while Marca.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            Marca.objects.create(
                nombre=nombre,
                slug=slug,
                descripcion=descripcion,
                activo=activo,
                imagen=imagen,
                mostrar_en_slider=mostrar_en_slider,
                orden_slider=orden_slider,
                imagen_slider=imagen_slider,
                imagen_slider_movil=imagen_slider_movil,
            )

            messages.success(request, f'Marca "{nombre}" creada exitosamente.')
            return redirect('productos:panel_admin_brands')

    return render(request, 'panel_admin/brand_add.html')


@staff_member_required(login_url='usuarios:login')
def panel_admin_brand_edit(request, brand_id):
    marca = get_object_or_404(Marca, pk=brand_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('estado', 'True') == 'True'
        remove_imagen = request.POST.get('remove_imagen')
        nueva_imagen = request.FILES.get('imagen')
        mostrar_en_slider = request.POST.get('mostrar_en_slider') == 'on'
        orden_slider = int(request.POST.get('orden_slider', 0) or 0)
        remove_imagen_slider = request.POST.get('remove_imagen_slider')
        nueva_imagen_slider = request.FILES.get('imagen_slider')
        remove_imagen_slider_movil = request.POST.get('remove_imagen_slider_movil')
        nueva_imagen_slider_movil = request.FILES.get('imagen_slider_movil')


        if not nombre:
            messages.error(request, 'El nombre de la marca es obligatorio.')
        else:
            slug = slug_manual if slug_manual else marca.slug
            if slug != marca.slug:
                base_slug = slug
                counter = 1
                while Marca.objects.filter(slug=slug).exclude(pk=marca.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            marca.nombre = nombre
            marca.slug = slug
            marca.descripcion = descripcion
            marca.activo = activo
            marca.mostrar_en_slider = mostrar_en_slider
            marca.orden_slider = orden_slider

            if remove_imagen:
                marca.imagen = None
            if nueva_imagen:
                marca.imagen = nueva_imagen
            
            if remove_imagen_slider:
                marca.imagen_slider = None
            if nueva_imagen_slider:
                marca.imagen_slider = nueva_imagen_slider

            if remove_imagen_slider_movil:
                marca.imagen_slider_movil = None
            if nueva_imagen_slider_movil:
                marca.imagen_slider_movil = nueva_imagen_slider_movil

            marca.save()

            messages.success(request, f'Marca "{nombre}" actualizada exitosamente.')
            return redirect('productos:panel_admin_brands')

    return render(request, 'panel_admin/brand_edit.html', {
        'marca': marca,
    })


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_brand_delete(request, brand_id):
    marca = get_object_or_404(Marca, pk=brand_id)
    nombre = marca.nombre
    marca.delete()
    messages.success(request, f'Marca "{nombre}" eliminada correctamente.')
    return redirect('productos:panel_admin_brands')


# ══════════════════════════════════════════════════════
# PANEL ADMIN — COLECCIONES
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_admin_collections(request):
    """
    Listado de colecciones para el panel administrativo.
    Incluye búsqueda y conteo de productos asociados.
    """
    search = request.GET.get('q', '').strip()
    colecciones = Coleccion.objects.annotate(
        num_productos=Count('productos', distinct=True)
    )
    if search:
        colecciones = colecciones.filter(nombre__icontains=search)
    colecciones = colecciones.order_by('nombre')

    return render(request, 'panel_admin/collection_list.html', {
        'colecciones': colecciones,
        'search': search,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_collection_add(request):

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('estado', 'True') == 'True'
        destacada = request.POST.get('destacada') == 'on'
        imagen = request.FILES.get('imagen') or None
        es_promocion = request.POST.get('es_promocion') == 'on'
        texto_anuncio = request.POST.get('texto_anuncio', '').strip() if es_promocion else ''

        if not nombre:
            messages.error(request, 'El nombre de la colección es obligatorio.')
        elif Coleccion.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe una colección con el nombre "{nombre}".')
        else:
            slug = slug_manual if slug_manual else slugify(nombre)
            base_slug = slug
            counter = 1
            while Coleccion.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            Coleccion.objects.create(
                nombre=nombre,
                slug=slug,
                descripcion=descripcion,
                activo=activo,
                destacada=destacada,
                imagen=imagen,
                es_promocion=es_promocion,       # ← añadido
                texto_anuncio=texto_anuncio,     # ← añadido
            )
            messages.success(request, f'Colección "{nombre}" creada exitosamente.')
            return redirect('productos:panel_admin_collections')

    return render(request, 'panel_admin/collection_add.html')


@staff_member_required(login_url='usuarios:login')
def panel_admin_collection_edit(request, coleccion_id):
    """
    Formulario para editar una colección existente.
    """
    coleccion = get_object_or_404(Coleccion, pk=coleccion_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        activo = request.POST.get('estado', 'True') == 'True'
        destacada = request.POST.get('destacada') == 'on'
        remove_imagen = request.POST.get('remove_imagen')
        nueva_imagen = request.FILES.get('imagen')
        es_promocion = request.POST.get('es_promocion') == 'on'
        texto_anuncio = request.POST.get('texto_anuncio', '').strip()

        coleccion.es_promocion = es_promocion
        coleccion.texto_anuncio = texto_anuncio if es_promocion else ''

        if not nombre:
            messages.error(request, 'El nombre de la colección es obligatorio.')
        elif Coleccion.objects.filter(nombre__iexact=nombre).exclude(pk=coleccion_id).exists():
            messages.error(request, f'Ya existe otra colección con el nombre "{nombre}".')
        else:
            slug = slug_manual if slug_manual else coleccion.slug
            if slug != coleccion.slug:
                base_slug = slug
                counter = 1
                while Coleccion.objects.filter(slug=slug).exclude(pk=coleccion.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            coleccion.nombre = nombre
            coleccion.slug = slug
            coleccion.descripcion = descripcion
            coleccion.activo = activo
            coleccion.destacada = destacada

            if remove_imagen:
                coleccion.imagen = None
            if nueva_imagen:
                coleccion.imagen = nueva_imagen

            coleccion.save()
            messages.success(request, f'Colección "{nombre}" actualizada exitosamente.')
            return redirect('productos:panel_admin_collections')

    return render(request, 'panel_admin/collection_edit.html', {
        'coleccion': coleccion,
    })


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_collection_delete(request, coleccion_id):
    """
    Elimina una colección. Solo acepta POST.
    Avisa si tiene productos asociados (los desvincula, no los borra).
    """
    coleccion = get_object_or_404(Coleccion, pk=coleccion_id)
    nombre = coleccion.nombre
    num_productos = coleccion.productos.count()
    coleccion.delete()
    if num_productos:
        messages.warning(
            request,
            f'Colección "{nombre}" eliminada. {num_productos} producto(s) quedaron sin colección asignada.'
        )
    else:
        messages.success(request, f'Colección "{nombre}" eliminada correctamente.')
    return redirect('productos:panel_admin_collections')


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_product_delete(request, producto_id):
    """
    Elimina un producto. Solo acepta POST.
    """
    producto = get_object_or_404(Producto, pk=producto_id)
    nombre = producto.nombre
    producto.delete()
    messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
    return redirect('productos:panel_admin_products')


# ══════════════════════════════════════════════════════
# PANEL ADMIN — CATEGORÍAS
# ══════════════════════════════════════════════════════

@staff_member_required(login_url='usuarios:login')
def panel_admin_categories(request):
    """
    Listado de categorias para el panel administrativo.
    Soporta filtro de busqueda y navegacion por categorias padre.
    """
    search = request.GET.get('q', '').strip()
    padre_id = request.GET.get('padre')
    categoria_padre = None

    categorias = Categoria.objects.select_related('padre').annotate(
        num_subcategorias=Count('subcategorias', distinct=True),
        num_productos=Count('productos', distinct=True),
    )

    if padre_id:
        categoria_padre = get_object_or_404(Categoria, pk=padre_id)
        categorias = categorias.filter(padre=categoria_padre)
    else:
        categorias = categorias.filter(padre__isnull=True)

    if search:
        categorias = categorias.filter(nombre__icontains=search)

    categorias = categorias.order_by('posicion', 'nombre')

    return render(request, 'panel_admin/category_list.html', {
        'categorias': categorias,
        'categoria_padre': categoria_padre,
        'search': search,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_category_add(request):
    """
    Formulario para crear una nueva categoría.
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        padre_id = request.POST.get('padre') or None
        activo = request.POST.get('estado', 'True') == 'True'
        posicion = request.POST.get('posicion', 0)

        if not nombre:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        else:
            slug = slug_manual if slug_manual else slugify(nombre)
            counter = 1
            base_slug = slug
            while Categoria.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            imagen = request.FILES.get('imagen') or None

            categoria = Categoria.objects.create(
                nombre=nombre,
                slug=slug,
                descripcion=descripcion,
                padre_id=padre_id,
                activo=activo,
                posicion=posicion,
                imagen=imagen,
            )
            messages.success(request, f'Categoría "{nombre}" creada exitosamente.')
            return redirect('productos:panel_admin_categories')

    categorias = Categoria.objects.filter(activo=True, padre__isnull=True).order_by('nombre')

    return render(request, 'panel_admin/category_add.html', {
        'categorias': categorias,
    })


@staff_member_required(login_url='usuarios:login')
def panel_admin_category_edit(request, categoria_id):
    """
    Formulario para editar una categoría existente.
    """
    categoria = get_object_or_404(Categoria, pk=categoria_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        slug_manual = request.POST.get('slug', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        padre_id = request.POST.get('padre') or None
        activo = request.POST.get('estado', 'True') == 'True'
        posicion = request.POST.get('posicion', categoria.posicion)
        remove_imagen = request.POST.get('remove_imagen')

        if not nombre:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
        else:
            slug = slug_manual if slug_manual else categoria.slug
            if slug != categoria.slug:
                counter = 1
                base_slug = slug
                while Categoria.objects.filter(slug=slug).exclude(pk=categoria.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            categoria.nombre = nombre
            categoria.slug = slug
            categoria.descripcion = descripcion
            categoria.padre_id = padre_id
            categoria.activo = activo
            categoria.posicion = posicion

            if remove_imagen:
                categoria.imagen = None

            nueva_imagen = request.FILES.get('imagen')
            if nueva_imagen:
                categoria.imagen = nueva_imagen

            categoria.save()
            messages.success(request, f'Categoría "{nombre}" actualizada exitosamente.')
            return redirect('productos:panel_admin_categories')

    categorias = Categoria.objects.filter(
        activo=True, padre__isnull=True
    ).exclude(pk=categoria_id).order_by('nombre')

    return render(request, 'panel_admin/category_edit.html', {
        'categoria': categoria,
        'categorias': categorias,
        # colecciones ya no aplica a Categoria — se asigna en el Producto
    })


@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_category_delete(request, categoria_id):
    """
    Elimina una categoría. Solo acepta POST.
    """
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    nombre = categoria.nombre
    categoria.delete()
    messages.success(request, f'Categoría "{nombre}" eliminada correctamente.')
    return redirect('productos:panel_admin_categories')

class MarcaListView(ListView):
    model = Producto
    template_name = 'shop-fullwidth.html'
    context_object_name = 'productos'

    def get_queryset(self):
        self.marca = get_object_or_404(Marca, slug=self.kwargs['slug'], activo=True)
        return Producto.objects.filter(marca=self.marca, activo=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # ← 8 espacios
        context['marca_actual'] = self.marca           # ← 8 espacios
        context['titulo'] = self.marca.nombre          # ← 8 espacios
        return context                                 # ← 8 espacios
# ══════════════════════════════════════════════════════
# CATÁLOGO - CLASS BASED VIEWS
# ══════════════════════════════════════════════════════

class ProductoListView(ListView):
    model = Producto
    template_name = 'shop-fullwidth.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        qs = Producto.objects.filter(
            activo=True
        ).prefetch_related('imagenes').select_related('categoria', 'coleccion', 'marca')

        # --- Búsqueda por texto ---
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(marca__nombre__icontains=q) |
                Q(categoria__nombre__icontains=q) |
                Q(material__icontains=q) |
                Q(descripcion_corta__icontains=q)
            )  # ← paréntesis de cierre que faltaba

        # --- Categoría (incluye subcategorías) ---
        categoria_slug = self.request.GET.get('categoria')
        if categoria_slug:
            try:
                cat = Categoria.objects.get(slug=categoria_slug, activo=True)
                subcats = cat.subcategorias.values_list('id', flat=True)
                qs = qs.filter(Q(categoria=cat) | Q(categoria__id__in=subcats))
            except Categoria.DoesNotExist:
                pass

        # --- Marca ---
        marca_slug = self.request.GET.get('marca')
        if marca_slug:
            qs = qs.filter(marca__slug=marca_slug)

        # --- Material ---
        material = self.request.GET.get('material')
        if material:
            qs = qs.filter(material__iexact=material)

        # --- Oferta ---
  
        oferta = self.request.GET.get('oferta')
        if oferta == 'si':
            qs = qs.exclude(precio_oferta__isnull=True).filter(
                precio_oferta__lt=F('precio')   # ← sin models.
            )
        elif oferta == 'no':
            qs = qs.filter(
                Q(precio_oferta__isnull=True) | Q(precio_oferta__gte=F('precio'))  # ← sin models.
            )

        orden = self.request.GET.get('orden', '')
        orden_map = {
            'a-z':         'nombre',
            'z-a':         '-nombre',
            'precio-asc':  'precio',
            'precio-desc': '-precio',
        }
        qs = qs.order_by(orden_map.get(orden, '-created_at'))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Búsqueda activa ---
        q = self.request.GET.get('q', '').strip()
        context['q'] = q
        context['titulo'] = f'Resultados para "{q}"' if q else 'Todos los Productos'

        # --- Título por categoría / marca ---
        categoria_slug = self.request.GET.get('categoria')
        if categoria_slug:
            try:
                context['categoria_actual'] = Categoria.objects.get(slug=categoria_slug, activo=True)
            except Categoria.DoesNotExist:
                pass

        marca_slug = self.request.GET.get('marca')
        if marca_slug:
            try:
                context['marca_actual'] = Marca.objects.get(slug=marca_slug, activo=True)
            except Marca.DoesNotExist:
                pass

        # --- Datos para el panel de filtros ---
        context['categorias'] = (
            Categoria.objects
            .filter(activo=True, padre=None)
            .prefetch_related('subcategorias')
        )
        context['marcas']     = Marca.objects.filter(activo=True).order_by('nombre')
        context['materiales'] = (
            Producto.objects
            .filter(activo=True, material__isnull=False)
            .exclude(material='')
            .values_list('material', flat=True)
            .distinct()
            .order_by('material')
        )

        # --- Filtros activos para el template ---
        context['categoria_activa'] = self.request.GET.get('categoria', '')
        context['marca_activa']     = self.request.GET.get('marca', '')
        context['material_activo']  = self.request.GET.get('material', '')
        context['oferta_activa']    = self.request.GET.get('oferta', '')

        return context

class ProductoDetailView(DetailView):
    """
    Vista detallada de un producto.
    Muestra información, atributos, imágenes y productos relacionados.
    """
    model = Producto
    template_name = 'detalle.html'
    context_object_name = 'producto'
    slug_field = 'slug'

    def get_queryset(self):
        return Producto.objects.filter(activo=True).select_related(
            'marca', 'categoria', 'coleccion'
        ).prefetch_related('imagenes', 'atributos__atributo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # ← 4 espacios adentro
        producto = self.object
        
        context['relacionados'] = Producto.objects.filter(
            categoria=producto.categoria,
            activo=True
        ).exclude(pk=producto.pk)[:8].select_related('marca').prefetch_related('imagenes')
        
        context['atributos'] = producto.atributos.select_related('atributo')
        
        return context


class CategoriaListView(ListView):
    """
    Lista productos de una categoría específica.
    Incluye subcategorías.
    """
    model = Producto
    template_name = 'shop-fullwidth.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        self.categoria = get_object_or_404(Categoria, slug=self.kwargs['slug'], activo=True)
        
        # Incluye subcategorías
        categorias = [self.categoria]
        categorias.extend(self.categoria.subcategorias.all())
        
        return Producto.objects.filter(
            categoria__in=categorias,
            activo=True
        ).prefetch_related('imagenes').select_related('categoria', 'marca')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Categoría: {self.categoria.nombre}'
        context['categoria_actual'] = self.categoria
        context['categorias'] = Categoria.objects.filter(activo=True, padre=None)
        return context


class ColeccionListView(ListView):
    """
    Lista productos de una colección específica.
    """
    model = Producto
    template_name = 'shop-fullwidth.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        self.coleccion = get_object_or_404(Coleccion, slug=self.kwargs['slug'], activo=True)
        return Producto.objects.filter(
            coleccion=self.coleccion,
            activo=True
        ).prefetch_related('imagenes').select_related('categoria', 'marca')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Colección: {self.coleccion.nombre}'
        context['coleccion_actual'] = self.coleccion
        context['categorias'] = Categoria.objects.filter(activo=True, padre=None)
        return context


# ══════════════════════════════════════════════════════
# CARRITO - SESSION & DB BASED
# ══════════════════════════════════════════════════════
from .cart import Cart
import json

def view_cart(request):
    """
    Vista de la página principal del carrito.
    """
    cart = Cart(request)
    # Recomendados: podríamos mostrar productos de la misma categoría o destacados
    productos_recomendados = Producto.objects.filter(activo=True, destacado=True).prefetch_related('imagenes')[:8]
    return render(request, 'view-cart.html', {
        'cart': cart,
        'cart_items': cart,
        'productos_recomendados': productos_recomendados
    })

@require_POST
def cart_add(request):
    """
    Añade un producto al carrito (AJAX).
    """
    cart = Cart(request)
    producto_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        producto = get_object_or_404(Producto, id=producto_id, activo=True)
        # Verificar stock
        if not producto.tiene_stock():
            return JsonResponse({'success': False, 'message': 'Producto sin stock.'})
            
        cart.add(producto=producto, quantity=quantity)
        
        return JsonResponse({
            'success': True,
            'message': 'Producto añadido correctamente.',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def cart_add_gift(request):
    """
    Añade un aporte (regalo) de Plan de Novios al carrito (AJAX).
    """
    cart = Cart(request)
    plan_id = request.POST.get('plan_id')
    nombres_novios = request.POST.get('nombres_novios')
    nombre_invitado = request.POST.get('nombre_invitado')
    mensaje = request.POST.get('mensaje', '')
    monto = request.POST.get('monto')
    quantity = int(request.POST.get('quantity', 1))
    
    # Parámetros opcionales si es un producto físico
    producto_id = request.POST.get('producto_id')
    nombre_producto = request.POST.get('nombre_producto')
    imagen_url = request.POST.get('imagen_url')
    
    if not all([plan_id, nombres_novios, nombre_invitado, monto]):
        return JsonResponse({'success': False, 'message': 'Faltan datos obligatorios para el regalo.'})
        
    try:
        cart.add_gift(
            plan_id=plan_id,
            nombres_novios=nombres_novios,
            nombre_invitado=nombre_invitado,
            mensaje=mensaje,
            monto=monto,
            quantity=quantity,
            producto_id=producto_id,
            nombre_producto=nombre_producto,
            imagen_url=imagen_url
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Regalo añadido al carrito correctamente.',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def cart_update(request):
    """
    Actualiza la cantidad de un producto (AJAX).
    """
    cart = Cart(request)
    producto_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        if quantity > 0:
            cart.update_quantity(producto_id, quantity)
        else:
            cart.remove(producto_id)
            
        # Calcular el total del item actualizado
        item_total = '0.00'
        for item in cart:
            if str(item['producto_id']) == str(producto_id):
                item_total = str(item['total'])
                break
                
        return JsonResponse({
            'success': True,
            'message': 'Carrito actualizado.',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price()),
            'item_total': item_total
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@require_POST
def cart_remove(request):
    """
    Elimina un producto del carrito (AJAX).
    """
    cart = Cart(request)
    producto_id = request.POST.get('product_id')
    
    try:
        cart.remove(producto_id)
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado.',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ══════════════════════════════════════════════════════
# CHECKOUT
# ══════════════════════════════════════════════════════

def checkout(request):
    """
    Vista de la página de Checkout.
    """
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Tu carrito está vacío. Añade productos para comprar.")
        return redirect('productos:view_cart')

    # Provincias y ciudades mockeadas para el formulario
    provincias = [
        {'id': 1, 'nombre': 'Pichincha'},
        {'id': 2, 'nombre': 'Guayas'},
        {'id': 3, 'nombre': 'Azuay'},
        {'id': 4, 'nombre': 'El Oro'},
    ]
    ciudades = [
        {'nombre': 'Quito', 'provincia': {'id': 1}},
        {'nombre': 'Guayaquil', 'provincia': {'id': 2}},
        {'nombre': 'Cuenca', 'provincia': {'id': 3}},
        {'nombre': 'Machala', 'provincia': {'id': 4}},
    ]

    context = {
        'cart': cart,
        'cart_items': cart,
        'provincias': provincias,
        'ciudades': ciudades,
    }
    
    # Pre-llenar datos si el usuario está autenticado
    if request.user.is_authenticated:
        context['user_nombre'] = getattr(request.user, 'nombre', '')
        context['user_apellido'] = getattr(request.user, 'apellido', '')
        context['user_email'] = request.user.email
        context['user_telefono'] = getattr(request.user, 'telefono', '')
        
        if request.user.provincia:
            context['user_provincia'] = request.user.provincia.nombre
        if request.user.ciudad:
            context['user_ciudad'] = request.user.ciudad.nombre

    return render(request, 'checkout.html', context)

@require_POST
def validate_discount_code(request):
    """
    Valida un cupón de descuento.
    """
    code = request.POST.get('discount_code', '').strip().upper()
    cart = Cart(request)
    subtotal = cart.get_total_price()
    
    # Mock de cupones válidos
    if code == 'LIVEN10':
        discount_amount = float(subtotal) * 0.10
        return JsonResponse({
            'valid': True,
            'discount_type': 'percentage',
            'discount_value': '10',
            'discount_amount': discount_amount
        })
    elif code == 'BIENVENIDO5':
        discount_amount = 5.00
        return JsonResponse({
            'valid': True,
            'discount_type': 'fixed',
            'discount_value': '5.00',
            'discount_amount': discount_amount
        })
        
    return JsonResponse({'valid': False, 'message': 'El cupón no es válido o ha expirado.'})

@require_POST
def checkout_process(request):
    """
    Procesa el formulario de checkout y simula la creación del pedido.
    """
    try:
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('productos:view_cart')

        # Aquí capturaríamos los datos de facturación
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telefono = request.POST.get('phone')
        pais = request.POST.get('country', 'Ecuador')
        
        ciudad = request.POST.get('city')
        if ciudad == 'Otra':
            ciudad = request.POST.get('other_city')
            
        direccion = request.POST.get('address')
        codigo_postal = request.POST.get('postal_code')
        notas = request.POST.get('order_note', '')
        metodo_pago = request.POST.get('payment_method', 'bank_transfer')
        print("METODO PAGO RECIBIDO:", metodo_pago, flush=True)
        print("PAYPHONE_TOKEN OK:", bool(settings.PAYPHONE_TOKEN), flush=True)
        print("PAYPHONE_CLIENT_ID OK:", bool(settings.PAYPHONE_CLIENT_ID), flush=True)
        print("PAYPHONE_CLIENT_SECRET OK:", bool(settings.PAYPHONE_CLIENT_SECRET), flush=True)
        print("PAYPHONE_APP_ID OK:", bool(settings.PAYPHONE_APP_ID), flush=True)
        print("PAYPHONE_ENCODING_PASSWORD OK:", bool(settings.PAYPHONE_ENCODING_PASSWORD), flush=True)
        print("PAYPHONE_PREPARE_URL:", settings.PAYPHONE_PREPARE_URL, flush=True)
        print("PAYPHONE_CONFIRM_URL:", settings.PAYPHONE_CONFIRM_URL, flush=True)
        print("PAYPHONE_RESPONSE_URL:", settings.PAYPHONE_RESPONSE_URL, flush=True)
        print("PAYPHONE_CANCEL_URL:", settings.PAYPHONE_CANCEL_URL, flush=True)

        # Recopilar notas de regalos
        notas_regalos = ""
        for item in cart:
            if item.get('is_gift'):
                detalle = item.get('detalle_producto', 'Efectivo')
                notas_regalos += f"Regalo: {item['nombre']} ({detalle}) | De: {item.get('nombre_invitado', '')} | Mensaje: {item.get('mensaje', '')}\n"
                
        if notas_regalos:
            notas = notas_regalos + ("\nNotas adicionales: " + notas if notas else "")

        # Crear el Pedido
        pedido = Pedido.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            nombres=first_name,
            apellidos=last_name,
            email=email,
            telefono=telefono,
            pais=pais,
            ciudad=ciudad,
            direccion=direccion,
            codigo_postal=codigo_postal,
            notas=notas,
            subtotal=cart.get_total_price(),
            total=cart.get_total_price(),  # Se puede aplicar envío y descuento
            estado='pendiente',
            metodo_pago=metodo_pago
        )

        # Crear los PedidoItem y registrar Movimientos
        has_gifts = False
        from apps.planes.models import SolicitudPlanNovios, MovimientoPlan
        
        for item in cart:
            if item.get('is_gift'):
                has_gifts = True
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=None,
                    nombre_producto=item['nombre'],
                    precio=item['precio'],
                    cantidad=item['quantity']
                )
                # Registrar Movimiento en el Plan de Novios
                try:
                    from decimal import Decimal
                    plan_id = item.get('plan_id')
                    if plan_id:
                        plan = SolicitudPlanNovios.objects.filter(id=plan_id).first()
                        if plan:
                            MovimientoPlan.objects.create(
                                plan=plan,
                                producto_id=item.get('producto_id'), # Puede ser None si es efectivo
                                monto=Decimal(item['precio']) * item['quantity'],
                                descripcion=f"Aporte de {item.get('nombre_invitado', 'Invitado')}: {item.get('mensaje', '')}"
                            )
                            # Actualizar campo estático por redundancia
                            plan.saldo_acumulado += Decimal(item['precio']) * item['quantity']
                            plan.save()
                except Exception as e:
                    print(f"Error registrando movimiento de regalo: {e}", flush=True)
                    
            else:
                producto_obj = item['producto']
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=producto_obj,
                    nombre_producto=producto_obj.nombre if producto_obj else item.get('nombre', 'Producto'),
                    precio=item['precio'],
                    cantidad=item['quantity']
                )
                # Bajo pedido: no reducimos stock
                pass
        
        # ── Enviar Notificación WhatsApp al Administrador si hay regalos ──
        if has_gifts:
            try:
                from .whatsapp_utils import enviar_mensaje_admin_nuevo_regalo
                enviar_mensaje_admin_nuevo_regalo(pedido)
            except Exception as e:
                print(f"Error enviando WhatsApp al admin: {e}", flush=True)
        
        if metodo_pago == 'bank_transfer':
            # En pago por transferencia el pedido queda creado y el carrito se puede limpiar.
            cart.clear()
            return redirect('productos:order_confirmation', pedido_id=pedido.id)

        if metodo_pago == 'payphone':
            try:
                print("ENTRANDO A BLOQUE PAYPHONE", flush=True)
                print("PAYPHONE PREPARE URL:", settings.PAYPHONE_PREPARE_URL, flush=True)
                print("PAYPHONE RESPONSE URL:", settings.PAYPHONE_RESPONSE_URL, flush=True)
                print("PAYPHONE CANCEL URL:", settings.PAYPHONE_CANCEL_URL, flush=True)
                payphone_data = preparar_pago_payphone(pedido)
                print("PEDIDO CREADO:", pedido.id, flush=True)
                print("PAYPHONE DATA:", payphone_data, flush=True)
                print("PAYPHONE DATA KEYS:", payphone_data.keys() if isinstance(payphone_data, dict) else type(payphone_data), flush=True)
                direct_url = (
                    payphone_data.get('payWithPayPhone') or
                    payphone_data.get('payWithCard') or
                    payphone_data.get('paymentUrl') or
                    payphone_data.get('payUrl') or
                    payphone_data.get('checkoutUrl') or
                    payphone_data.get('url') or
                    payphone_data.get('redirectUrl') or
                    payphone_data.get('payment_url')
                )
                if direct_url:
                    return redirect(direct_url)
                return redirect('productos:order_payment_payphone', pedido_id=pedido.id)
            except Exception as e:
                print("ERROR PAYPHONE EN CHECKOUT_PROCESS:", repr(e), flush=True)
                pedido.estado_pago = 'rechazado'
                pedido.estado = 'pendiente'
                pedido.payphone_response = {'error': str(e)}
                pedido.save(update_fields=['estado_pago', 'estado', 'payphone_response'])
                messages.error(request, f'Error PayPhone: {e}')
                return redirect('productos:checkout')

        # Si se introduce un metodo de pago no esperado, redirigir al checkout.
        messages.error(request, 'Método de pago no válido. Por favor, revisa tu selección.')
        return redirect('productos:checkout')
    except Exception as e:
        import traceback
        print("ERROR GENERAL CHECKOUT_PROCESS:", repr(e), flush=True)
        traceback.print_exc()
        messages.error(request, f"Error procesando checkout: {e}")
        return redirect("productos:checkout")

def order_payment_payphone(request, pedido_id):
    """
    Página de pago con datos públicos de PayPhone.
    """
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if pedido.estado == 'pagado':
        messages.info(request, "Este pedido ya ha sido pagado.")
        return redirect('productos:order_confirmation', pedido_id=pedido.id)

    payphone_data = pedido.payphone_response or {}
    payment_url = (
        payphone_data.get('payWithCard') or
        payphone_data.get('payWithPayPhone') or
        payphone_data.get('paymentUrl') or
        payphone_data.get('payUrl') or
        payphone_data.get('checkoutUrl') or
        payphone_data.get('url') or
        payphone_data.get('redirectUrl') or
        payphone_data.get('payment_url')
    )

    return render(request, 'payphone_payment.html', {
        'pedido': pedido,
        'payment_url': payment_url,
        'payphone_data': payphone_data,
    })


def payphone_respuesta(request):
    """Procesa la respuesta de PayPhone y confirma la transacción en backend."""
    transaction_id = (
        request.GET.get('id') or
        request.POST.get('id') or
        request.GET.get('transactionId') or
        request.POST.get('transactionId')
    )
    client_transaction_id = (
        request.GET.get('clientTransactionId') or
        request.POST.get('clientTransactionId') or
        request.GET.get('client_transaction_id') or
        request.POST.get('client_transaction_id')
    )

    if not client_transaction_id:
        messages.error(request, 'Respuesta inválida de PayPhone.')
        return redirect('productos:checkout')

    pedido = get_object_or_404(Pedido, payphone_client_transaction_id=client_transaction_id)

    try:
        confirm_data = confirmar_pago_payphone(transaction_id, client_transaction_id)
        pedido.payphone_response = confirm_data
        pedido.payphone_transaction_id = transaction_id
        pedido.payphone_authorization_code = (
            confirm_data.get('authorizationCode') or
            confirm_data.get('authorization_code') or
            confirm_data.get('authorization')
        )

        status = (confirm_data.get('status') or confirm_data.get('paymentStatus') or confirm_data.get('state') or '').lower()

        if status in ('approved', 'aprobado', 'paid', 'completed', 'completado'):
            pedido.estado = 'pagado'
            pedido.estado_pago = 'aprobado'
            pedido.transaccion_id = transaction_id
            pedido.save(update_fields=[
                'estado',
                'estado_pago',
                'transaccion_id',
                'payphone_transaction_id',
                'payphone_authorization_code',
                'payphone_response'
            ])

            try:
                Cart(request).clear()
            except Exception:
                pass

            messages.success(request, 'Pago aprobado. Gracias por tu compra.')
            return redirect('productos:order_confirmation', pedido_id=pedido.id)

        if status in ('cancelled', 'cancelado', 'canceled'):
            pedido.estado_pago = 'cancelado'
            pedido.estado = 'cancelado'
        elif status in ('rejected', 'rechazado', 'declined', 'denied'):
            pedido.estado_pago = 'rechazado'
            pedido.estado = 'pendiente'
        else:
            pedido.estado_pago = 'pendiente'

        pedido.save(update_fields=[
            'estado',
            'estado_pago',
            'payphone_transaction_id',
            'payphone_authorization_code',
            'payphone_response'
        ])
        return render(request, 'payphone_cancelled.html', {
            'pedido': pedido,
            'status': status,
            'confirm_data': confirm_data,
        })
    except Exception as e:
        pedido.estado_pago = 'rechazado'
        pedido.estado = 'pendiente'
        pedido.payphone_response = {'error': str(e)}
        pedido.save(update_fields=['estado', 'estado_pago', 'payphone_response'])
        messages.error(request, 'No se pudo confirmar el pago con PayPhone.')
        return render(request, 'payphone_cancelled.html', {
            'pedido': pedido,
            'status': 'error',
            'error_message': str(e),
        })


def payphone_cancelado(request):
    """Marca el pago como cancelado cuando PayPhone redirige al usuario fuera del flujo."""
    client_transaction_id = request.GET.get('clientTransactionId') or request.POST.get('clientTransactionId')
    pedido = None

    if client_transaction_id:
        pedido = Pedido.objects.filter(payphone_client_transaction_id=client_transaction_id).first()
        if pedido:
            pedido.estado_pago = 'cancelado'
            pedido.estado = 'cancelado'
            pedido.payphone_response = {
                'cancelled': True,
                'params': request.GET.dict() if request.method == 'GET' else request.POST.dict()
            }
            pedido.save(update_fields=['estado', 'estado_pago', 'payphone_response'])

    if pedido:
        messages.warning(request, 'Pago cancelado. Puedes intentar de nuevo o escoger otro método.')
        return render(request, 'payphone_cancelled.html', {'pedido': pedido, 'status': 'cancelado'})

    messages.warning(request, 'Pago cancelado o datos de transacción no encontrados.')
    return redirect('productos:checkout')


def order_confirmation(request, pedido_id):
    """
    Vista para mostrar la confirmación del pedido.
    Genera la URL de WhatsApp con factura profesional lista para el cliente.
    """
    from urllib.parse import quote
    from .models import Pedido
    from .whatsapp_utils import generar_mensaje_factura_cliente
    
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Verificar que el pedido pertenece al usuario (si está autenticado)
    if request.user.is_authenticated and pedido.usuario and pedido.usuario != request.user:
        messages.error(request, 'No tienes permiso para ver este pedido.')
        return redirect('home')

    # ── Generar URL de WhatsApp con mensaje de factura profesional ────────────
    whatsapp_url = ''
    try:
        # Usamos el numero de WhatsApp del admin de LivenShop
        numero_tienda = "593989387657"
        
        mensaje_factura = generar_mensaje_factura_cliente(pedido, request)
        numero_limpio = numero_tienda.replace('+', '').replace(' ', '').replace('-', '')
        mensaje_encoded = quote(mensaje_factura, encoding='utf-8')
        whatsapp_url = f"https://wa.me/{numero_limpio}?text={mensaje_encoded}"
    except Exception as e:
        whatsapp_url = 'https://wa.me/593989387657'

    context = {
        'pedido': pedido,
        'whatsapp_url': whatsapp_url,
    }

    return render(request, 'order-confirmation.html', context)


# ══════════════════════════════════════════════════════
# APIs / QUICK VIEW
# ══════════════════════════════════════════════════════

def producto_quick_view(request, producto_id):
    """
    API para mostrar quick view de un producto en modal.
    Retorna HTML o JSON con información del producto.
    """
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    
    # Obtiene todas las imágenes
    imagenes = []
    for img in producto.imagenes.all():
        imagenes.append({
            'src': img.src,
            'alt': producto.nombre,
            'es_principal': img.es_principal
        })
    
    # Atributos
    atributos = []
    for attr in producto.atributos.select_related('atributo'):
        atributos.append({
            'nombre': attr.atributo.nombre,
            'valor': attr.valor
        })
    
    # Verificar si está en la wishlist
    wishlist = request.session.get('wishlist', [])
    en_wishlist = str(producto.id) in [str(x) for x in wishlist]
    
    data = {
        'id': producto.id,
        'nombre': producto.nombre,
        'slug': producto.slug,
        'precio': str(producto.precio),
        'precio_oferta': str(producto.precio_oferta) if producto.precio_oferta else None,
        'precio_final': str(producto.precio_final()),
        'stock': producto.stock,
        'tiene_stock': producto.tiene_stock(),
        'tiene_oferta': producto.tiene_oferta(),
        'porcentaje_descuento': producto.porcentaje_descuento(),
        'descripcion_corta': producto.descripcion_corta or '',
        'descripcion_completa': producto.descripcion_completa or '',
        'imagenes': imagenes,
        'atributos': atributos,
        'categoria': producto.categoria.nombre if producto.categoria else '',
        'marca': producto.marca.nombre if producto.marca else '',
        'url_detalle': producto.get_absolute_url(),
        'en_wishlist': en_wishlist,
    }
    
    return JsonResponse(data)

# ══════════════════════════════════════════════════════
# WISHLIST (FAVORITOS)
# ══════════════════════════════════════════════════════
def view_wishlist(request):
    wishlist = request.session.get('wishlist', [])
    productos_favoritos = Producto.objects.filter(id__in=wishlist, activo=True).prefetch_related('imagenes')
    return render(request, 'my-account-wishlist.html', {
        'productos_favoritos': productos_favoritos
    })

@require_POST
def wishlist_toggle(request):
    producto_id = request.POST.get('product_id')
    if not producto_id:
        return JsonResponse({'success': False})
        
    try:
        producto_id = int(producto_id)
    except ValueError:
        return JsonResponse({'success': False})

    wishlist = request.session.get('wishlist', [])
    if producto_id in wishlist:
        wishlist.remove(producto_id)
        added = False
    else:
        wishlist.append(producto_id)
        added = True
        
    request.session['wishlist'] = wishlist
    request.session.modified = True
    
    return JsonResponse({'success': True, 'added': added, 'count': len(wishlist)})

# ══════════════════════════════════════════════════════
# PANEL ADMIN - PEDIDOS
# ══════════════════════════════════════════════════════
from django.core.paginator import Paginator

@staff_member_required(login_url='usuarios:login')
def panel_admin_orders(request):
    """
    Lista de pedidos en el panel de administración.
    """
    from .models import Pedido
    pedidos_list = Pedido.objects.all().order_by('-created_at')
    paginator = Paginator(pedidos_list, 20)
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)
    return render(request, 'panel_admin/order_list.html', {'pedidos': pedidos})

@staff_member_required(login_url='usuarios:login')
def panel_admin_order_detail(request, pedido_id):
    """
    Detalle de un pedido específico.
    """
    from .models import Pedido
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    return render(request, 'panel_admin/order_detail.html', {'pedido': pedido})

@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_order_update_status(request, pedido_id):
    """
    Actualiza el estado de un pedido (ej. pendiente -> pagado).
    """
    from .models import Pedido
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    nuevo_estado = request.POST.get('estado')
    if nuevo_estado in dict(Pedido.ESTADO_CHOICES):
        pedido.estado = nuevo_estado
        pedido.save()
        messages.success(request, f'Estado del pedido #{pedido.id} actualizado a {pedido.get_estado_display()}.')
    else:
        messages.error(request, 'Estado no válido.')
    return redirect('productos:panel_admin_orders')
