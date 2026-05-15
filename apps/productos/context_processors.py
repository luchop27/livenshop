from .models import Categoria, CarritoItem, Coleccion, Marca, ShopGramPost


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
def anuncios_bar(request):
    anuncios = Coleccion.objects.filter(
        activo=True,
        es_promocion=True
    ).exclude(
        texto_anuncio__isnull=True
    ).exclude(
        texto_anuncio__exact=''
    )

    return {
        'anuncios_bar': anuncios
    }