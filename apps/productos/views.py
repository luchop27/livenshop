from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .models import Producto, Categoria, Coleccion, CarritoItem


# ══════════════════════════════════════════════════════
# CATÁLOGO - CLASS BASED VIEWS
# ══════════════════════════════════════════════════════

class ProductoListView(ListView):
    """
    Lista todos los productos activos.
    """
    model = Producto
    template_name = 'productos/lista.html'
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
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'
    slug_field = 'slug'

    def get_queryset(self):
        return Producto.objects.filter(activo=True).prefetch_related(
            'imagenes', 'atributos__atributo'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.get_object()
        
        # Productos relacionados (misma categoría)
        context['relacionados'] = Producto.objects.filter(
            categoria=producto.categoria,
            activo=True
        ).exclude(pk=producto.pk)[:4].prefetch_related('imagenes')
        
        # Atributos organizados
        context['atributos'] = producto.atributos.select_related('atributo')
        
        return context


class CategoriaListView(ListView):
    """
    Lista productos de una categoría específica.
    Incluye subcategorías.
    """
    model = Producto
    template_name = 'productos/lista.html'
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
        context['categoria'] = self.categoria
        context['categorias'] = Categoria.objects.filter(activo=True, padre=None)
        return context


class ColeccionListView(ListView):
    """
    Lista productos de una colección específica.
    """
    model = Producto
    template_name = 'productos/lista.html'
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
        context['coleccion'] = self.coleccion
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
    
    # Obtiene imagen principal
    imagen_principal = producto.imagenes.filter(es_principal=True).first()
    if not imagen_principal:
        imagen_principal = producto.imagenes.first()
    
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
        'imagen': imagen_principal.src if imagen_principal else '',
        'categoria': producto.categoria.nombre if producto.categoria else '',
        'url_detalle': producto.get_absolute_url(),
    }
    
    return JsonResponse(data)
