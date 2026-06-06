from .models import Categoria, CarritoItem, Coleccion, Marca, ShopGramPost, TiendaConfig
from .cart import Cart

def menu_categorias(request):
    return {
        'menu_categorias': Categoria.objects.filter(
            activo=True,
            padre=None
        ).prefetch_related('subcategorias').order_by('posicion', 'nombre'),
        'menu_marcas': Marca.objects.filter(activo=True).order_by('nombre'),
    }

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

def tienda_config(request):
    """Exposes TiendaConfig singleton to all templates."""
    config = TiendaConfig.objects.first()
    if not config:
        # Create default config to avoid blank or crashing templates
        config = TiendaConfig.objects.create(
            direccion="1234 Fashion Street, Suite 567, New York, NY 10001",
            email="info@fashionshop.com",
            telefono="(212) 555-1234",
            horario_apertura="Nuestro almacén ha reabierto para compras, exchange Every day 11am to 7pm",
            mapa_embed_url="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d317859.6089702069!2d-0.075949!3d51.508112!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x48760349331f38dd%3A0xa8bf49dde1d56467!2sTower%20of%20London!5e0!3m2!1sen!2sus!4v1719221598456!5m2!1sen!2sus"
        )
    return {
        'tienda_config': config
    }