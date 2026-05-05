from .models import Categoria, CarritoItem, Marca

def menu_categorias(request):
    return {
        'menu_categorias': Categoria.objects.filter(
            activo=True,
            padre=None
        ).prefetch_related('subcategorias').order_by('posicion', 'nombre'),
        'menu_marcas': Marca.objects.filter(activo=True).order_by('nombre'),
    }

def carrito_count(request):
    count = 0
    if request.user.is_authenticated:
        count = CarritoItem.objects.filter(usuario=request.user).count()
    return {'carrito_count': count}