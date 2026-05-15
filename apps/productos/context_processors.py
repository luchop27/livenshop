from .models import Categoria, CarritoItem, Marca, ShopGramPost


def menu_categorias(request):
    return {
        'menu_categorias': Categoria.objects.filter(
            activo=True,
            padre=None
        ).prefetch_related('subcategorias').order_by('posicion', 'nombre'),
        'menu_marcas': Marca.objects.filter(activo=True).order_by('nombre'),
    }

from .cart import Cart

def carrito_count(request):
    cart = Cart(request)
    return {'cart': cart, 'carrito_count': len(cart)}
def shop_gram(request):
    return {
        'shop_gram_posts': ShopGramPost.objects.filter(activo=True)[:10]
    }