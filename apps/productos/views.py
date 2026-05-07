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
from .models import Producto, Categoria, Marca, Coleccion, CarritoItem
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from .models import Marca, Producto, Categoria, Coleccion, CarritoItem, Imagen, AtributoProducto, ShopGramPost, Pedido, PedidoItem


def _active_marcas():
    return Marca.objects.filter(activo=True).order_by('nombre')


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
    ).select_related('marca').prefetch_related('imagenes')[:12]
    
    # Categorías principales (sin padre)
    categorias = Categoria.objects.filter(
        activo=True,
        padre=None
    ).order_by('posicion', 'nombre')[:6]
    
    # Colecciones destacadas para el slider
    colecciones = Coleccion.objects.filter(activo=True, destacada=True)
    shop_gram_posts = ShopGramPost.objects.filter(activo=True)[:10]
    marcas = Marca.objects.filter(activo=True).order_by('nombre')
    return render(request, 'home.html', {
        'productos': productos,
        'categorias': categorias,
        'colecciones': colecciones,
        'shop_gram_posts': shop_gram_posts,\
        'marcas': marcas,
    })
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
        stock = request.POST.get('stock', '0')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_completa = request.POST.get('descripcion_completa', '').strip()
        marca_id = request.POST.get('marca') or None
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
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
        stock = request.POST.get('stock', '0')
        categoria_id = request.POST.get('categoria') or None
        coleccion_id = request.POST.get('coleccion') or None
        descripcion_corta = request.POST.get('descripcion_corta', '').strip()
        descripcion_completa = request.POST.get('descripcion_completa', '').strip()
        marca_id = request.POST.get('marca') or None
        material = request.POST.get('material', '').strip()
        dimensiones = request.POST.get('dimensiones', '').strip()
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

            if remove_imagen:
                marca.imagen = None
            if nueva_imagen:
                marca.imagen = nueva_imagen

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

class MarcaListView(ListView):
    model = Producto
    template_name = 'shop-fullwidth.html'  # el mismo template que usas para categoría
    context_object_name = 'productos'

    def get_queryset(self):
        self.marca = get_object_or_404(Marca, slug=self.kwargs['slug'], activo=True)
        return Producto.objects.filter(marca=self.marca, activo=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['marca'] = self.marca
        context['titulo'] = self.marca.nombre
        return context
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
        ).prefetch_related('imagenes').select_related('categoria', 'coleccion', 'marca')

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
        context['user_nombre'] = getattr(request.user, 'nombres', '')
        context['user_apellido'] = getattr(request.user, 'apellidos', '')
        context['user_email'] = request.user.email
        # Aquí podrías cargar teléfono u otros datos si los tienes en el modelo Usuario

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

    # Crear los PedidoItem
    for item in cart:
        producto_obj = item['producto']
        PedidoItem.objects.create(
            pedido=pedido,
            producto=producto_obj,
            nombre_producto=producto_obj.nombre,
            precio=item['precio'],
            cantidad=item['quantity']
        )
        # Opcional: reducir stock aquí o cuando el pedido sea pagado
        if producto_obj.stock >= item['quantity']:
            producto_obj.stock -= item['quantity']
            producto_obj.save()
    
    # Limpiar el carrito después de la compra
    cart.clear()
    
    if metodo_pago == 'bank_transfer':
        # Redirigir a página de confirmación
        return redirect('productos:order_confirmation', pedido_id=pedido.id)
    else:
        # Payphone redirect
        return redirect('productos:order_payment_payphone', pedido_id=pedido.id)

def order_payment_payphone(request, pedido_id):
    """
    Página de pago con botón Payphone.
    """
    from .models import Pedido
    pedido = get_object_or_404(Pedido, id=pedido_id)

    # Si ya está pagado, no mostrar el botón
    if pedido.estado == 'pagado':
        messages.info(request, "Este pedido ya ha sido pagado.")
        return redirect('home')

    return render(request, 'payphone_payment.html', {'pedido': pedido})

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
    return redirect('productos:panel_admin_order_detail', pedido_id=pedido.id)
