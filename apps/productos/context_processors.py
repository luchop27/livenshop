"""
Context Processors para la app de productos.

Proporciona datos globales a todos los templates sin necesidad de pasarlos
en cada vista.

IMPORTANTE: Registrar en settings.py en TEMPLATES > OPTIONS > context_processors
"""

from .models import Categoria, CarritoItem


def menu_categorias(request):
    """
    Proporciona las categorías principales (sin padre) con sus subcategorías.
    Disponible en todos los templates como {{ menu_categorias }}
    """
    return {
        'menu_categorias': Categoria.objects.filter(
            activo=True,
            padre=None
        ).prefetch_related('subcategorias').order_by('posicion', 'nombre')
    }


def carrito_count(request):
    """
    Proporciona el contador de items en el carrito.
    Disponible en todos los templates como {{ carrito_count }}
    """
    count = 0
    if request.user.is_authenticated:
        count = CarritoItem.objects.filter(usuario=request.user).count()
    
    return {'carrito_count': count}
