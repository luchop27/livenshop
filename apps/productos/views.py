from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib import messages
from django.utils.text import slugify

from .models import Producto, Categoria, Coleccion, CarritoItem, Imagen, AtributoProducto, ShopGramPost


# ══════════════════════════════════════════════════════
# HOME - FUNCTION BASED VIEW
# ══════════════════════════════════════════════════════

def home(request):
    """
    Vista de la página de inicio.
    Muestra productos destacados/trending, categorías principales y colecciones destacadas.
    """
    productos = Producto.objects.filter(
        activo=True
    ).prefetch_related('imagenes')[:12]
    
    # Categorías principales (sin padre)
    categorias = Categoria.objects.filter(
        activo=True,
        padre=None
    ).order_by('posicion', 'nombre')[:6]
    
    # Colecciones destacadas para el slider
    colecciones = Coleccion.objects.filter(activo=True, destacada=True)
    shop_gram_posts = ShopGramPost.objects.filter(activo=True)[:10]
    return render(request, 'home.html', {
        'productos': productos,
        'categorias': categorias,
        'colecciones': colecciones,
        'shop_gram_posts': shop_gram_posts
    })


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
        'categoria'
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
        'categoria', 'coleccion'
    ).prefetch_related('imagenes').order_by('-created_at')

    if search:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search) |
            Q(marca__icontains=search) |
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
        stock = request.POST.get('stock', '0')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_larga = request.POST.get('descripcion_larga', '').strip()
        marca = request.POST.get('marca', '').strip()
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
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
                precio=precio,
                precio_oferta=precio_oferta,
                stock=stock,
                categoria_id=categoria_id,
                coleccion_id=coleccion_id,
                descripcion_corta=descripcion_corta,
                descripcion_larga=descripcion_larga,
                marca=marca,
                material=material,
                dimensiones=dimensiones,
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

    return render(request, 'panel_admin/product_add.html', {
        'categorias': categorias,
        'colecciones': colecciones,
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
        stock = request.POST.get('stock', '0')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_larga = request.POST.get('descripcion_larga', '').strip()
        marca = request.POST.get('marca', '').strip()
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
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
            producto.precio = precio
            producto.precio_oferta = precio_oferta
            producto.stock = stock
            producto.categoria_id = categoria_id
            producto.coleccion_id = coleccion_id
            producto.descripcion_corta = descripcion_corta
            producto.descripcion_larga = descripcion_larga
            producto.marca = marca
            producto.material = material
            producto.dimensiones = dimensiones
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

    return render(request, 'panel_admin/product_edit.html', {
        'producto': producto,
        'categorias': categorias,
        'colecciones': colecciones,
    })


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

    categorias = Categoria.objects.select_related('coleccion', 'padre').annotate(
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
        coleccion_id = request.POST.get('coleccion') or None
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
                coleccion_id=coleccion_id,
                activo=activo,
                posicion=posicion,
                imagen=imagen,
            )
            messages.success(request, f'Categoría "{nombre}" creada exitosamente.')
            return redirect('productos:panel_admin_categories')

    categorias = Categoria.objects.filter(activo=True, padre__isnull=True).order_by('nombre')
    colecciones = Coleccion.objects.filter(activo=True).order_by('nombre')

    return render(request, 'panel_admin/category_add.html', {
        'categorias': categorias,
        'colecciones': colecciones,
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
        coleccion_id = request.POST.get('coleccion') or None
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
            categoria.coleccion_id = coleccion_id
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
    colecciones = Coleccion.objects.filter(activo=True).order_by('nombre')

    return render(request, 'panel_admin/category_edit.html', {
        'categoria': categoria,
        'categorias': categorias,
        'colecciones': colecciones,
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


# ══════════════════════════════════════════════════════
# CATÁLOGO - CLASS BASED VIEWS
# ══════════════════════════════════════════════════════

class ProductoListView(ListView):
    """
    Lista todos los productos activos.
    """
    model = Producto
    template_name = 'shop-fullwidth.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        return Producto.objects.filter(
            activo=True
        ).prefetch_related('imagenes').select_related('categoria', 'coleccion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Todos los Productos'
        context['categorias'] = Categoria.objects.filter(activo=True, padre=None)
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
        return Producto.objects.filter(activo=True).prefetch_related(
            'imagenes', 'atributos__atributo'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # ← 4 espacios adentro
        producto = self.object
        
        context['relacionados'] = Producto.objects.filter(
            categoria=producto.categoria,
            activo=True
        ).exclude(pk=producto.pk)[:8].prefetch_related('imagenes')
        
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
        ).prefetch_related('imagenes').select_related('categoria')

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
        ).prefetch_related('imagenes').select_related('categoria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Colección: {self.coleccion.nombre}'
        context['coleccion_actual'] = self.coleccion
        context['categorias'] = Categoria.objects.filter(activo=True, padre=None)
        return context


# ══════════════════════════════════════════════════════
# CARRITO - CLASS BASED & FUNCTION BASED VIEWS
# ══════════════════════════════════════════════════════

class CarritoView(ListView):
    """
    Vista del carrito de compras.
    Solo accesible para usuarios autenticados.
    """
    model = CarritoItem
    template_name = 'productos/carrito.html'
    context_object_name = 'items'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return CarritoItem.objects.filter(
            usuario=self.request.user
        ).select_related('producto').prefetch_related('producto__imagenes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.get_queryset()
        
        # Calcula totales
        total = sum(item.total_precio for item in items)
        cantidad_items = items.count()
        
        context['total'] = total
        context['cantidad_items'] = cantidad_items
        context['hay_items'] = cantidad_items > 0
        
        return context


@login_required
def agregar_al_carrito(request, producto_id):
    """
    Añade un producto al carrito o incrementa su cantidad.
    Responde con JSON para AJAX.
    """
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    
    item, created = CarritoItem.objects.get_or_create(
        usuario=request.user,
        producto=producto,
        defaults={
            'precio': producto.precio_final(),
            'cantidad': 1
        }
    )
    
    if not created:
        item.cantidad += 1
        item.precio = producto.precio_final()
        item.save()
    
    # Calcula el contador total del carrito
    carrito_count = CarritoItem.objects.filter(usuario=request.user).count()
    
    return JsonResponse({
        'ok': True,
        'cantidad': item.cantidad,
        'carrito_count': carrito_count,
        'total_item': str(item.total_precio),
        'mensaje': f'Producto añadido al carrito (x{item.cantidad})'
    })


@login_required
def eliminar_del_carrito(request, item_id):
    """
    Elimina un item del carrito.
    """
    CarritoItem.objects.filter(pk=item_id, usuario=request.user).delete()
    return redirect('productos:carrito')


@login_required
@require_http_methods(["POST"])
def actualizar_cantidad(request):
    """
    Actualiza la cantidad de un item del carrito.
    Acepta JSON o form data.
    """
    try:
        item_id = int(request.POST.get('item_id', 0))
        cantidad = int(request.POST.get('cantidad', 1))
        
        item = get_object_or_404(CarritoItem, pk=item_id, usuario=request.user)
        
        if cantidad > 0:
            item.cantidad = cantidad
            item.save()
            resultado = {
                'ok': True,
                'cantidad': item.cantidad,
                'total_item': str(item.total_precio)
            }
        else:
            item.delete()
            resultado = {'ok': True, 'eliminado': True}
        
        return JsonResponse(resultado)
    
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)


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
        'descripcion_larga': producto.descripcion_larga or '',
        'imagenes': imagenes,
        'atributos': atributos,
        'categoria': producto.categoria.nombre if producto.categoria else '',
        'url_detalle': producto.get_absolute_url(),
    }
    
    return JsonResponse(data)
