from decimal import Decimal
from django.conf import settings
from apps.productos.models import Producto, CarritoItem

class Cart:
    """
    Clase para manejar el carrito de compras en la sesión y BD.
    Si el usuario está autenticado, sincroniza con CarritoItem en la BD.
    """
    
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user
        
        # Siempre inicializar desde la sesión para no perder items temporales (como regalos)
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

        # Si el usuario está autenticado, sincronizar con la BD
        if self.user.is_authenticated:
            self._load_from_db()
    
    def _load_from_db(self):
        """
        Carga items de la BD y los mezcla con los de la sesión.
        Los regalos se mantienen en la sesión (ya que CarritoItem no los soporta actualmente).
        """
        items_db = CarritoItem.objects.filter(usuario=self.user).select_related('producto')
        
        # Preservamos lo que ya hay en la sesión (como regalos u otros items añadidos en este request)
        for item in items_db:
            product_key = str(item.producto_id)
            
            # Solo cargamos de la BD si no estaba ya en la sesión (o si queremos que la BD mande)
            # Generalmente en Liven, la BD es el estado persistente de productos físicos.
            self.cart[product_key] = {
                'producto_id': item.producto_id,
                'nombre': item.producto.nombre,
                'producto_slug': item.producto.slug,
                'precio': str(item.precio),
                'quantity': item.cantidad,
                'imagen': item.imagen_url,
                '_db_id': item.id
            }
            
    def _save_to_db(self):
        if not self.user.is_authenticated:
            return
            
        # Solo sincronizar items que NO sean regalos (ya que regalos no tienen producto_id real)
        valid_items = {k: v for k, v in self.cart.items() if not k.startswith('_') and isinstance(v, dict) and not v.get('is_gift')}
        existing_db_ids = {item['_db_id'] for item in valid_items.values() if '_db_id' in item}
        
        CarritoItem.objects.filter(usuario=self.user).exclude(id__in=existing_db_ids).delete()
        
        for product_key, item_data in valid_items.items():
            producto_id = item_data['producto_id']
            cantidad = item_data['quantity']
            precio = Decimal(item_data['precio'])
            imagen_url = item_data.get('imagen')
            
            if '_db_id' in item_data:
                try:
                    carrito_item = CarritoItem.objects.get(id=item_data['_db_id'])
                    carrito_item.cantidad = cantidad
                    carrito_item.save()
                except CarritoItem.DoesNotExist:
                    CarritoItem.objects.get_or_create(
                        usuario=self.user,
                        producto_id=producto_id,
                        defaults={'cantidad': cantidad, 'precio': precio, 'imagen_url': imagen_url}
                    )
            else:
                CarritoItem.objects.get_or_create(
                    usuario=self.user,
                    producto_id=producto_id,
                    defaults={'cantidad': cantidad, 'precio': precio, 'imagen_url': imagen_url}
                )

    def add(self, producto, quantity=1, override_quantity=False):
        product_id = str(producto.id)
        
        if product_id not in self.cart:
            precio = producto.precio_final()
            primera_imagen = producto.imagenes.first()
            imagen_url = primera_imagen.imagen.url if primera_imagen and primera_imagen.imagen else None
            
            self.cart[product_id] = {
                'producto_id': producto.id,
                'producto_slug': producto.slug,
                'nombre': producto.nombre,
                'precio': str(precio),
                'quantity': 0,
                'imagen': imagen_url,
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        self.save()

    def add_gift(self, plan_id, nombres_novios, nombre_invitado, mensaje, monto, quantity=1, producto_id=None, nombre_producto=None, imagen_url=None):
        """Agrega un aporte de regalo al carrito. Puede ser efectivo (sin producto) o un producto físico específico."""
        import time
        gift_key = f"gift_{plan_id}_{int(time.time())}"
        
        # El nombre que ve el INVITADO en el carrito es más romántico/genérico
        display_name = f"Aporte al Plan de Novios: {nombres_novios}"
        
        # Formatear nombres para la tarjeta del carrito
        nombres_html = nombres_novios.replace(" y ", " <span>&</span> ").replace(" Y ", " <span>&</span> ")
        
        self.cart[gift_key] = {
            'is_gift': True,
            'plan_id': plan_id,
            'nombres_novios': nombres_novios,
            'nombres_novios_html': nombres_html,
            'nombre_invitado': nombre_invitado,
            'mensaje': mensaje,
            'precio': str(monto),
            'quantity': quantity,
            'nombre': display_name,
            'detalle_producto': nombre_producto if nombre_producto else "Efectivo",
            'imagen': imagen_url,
            'producto_slug': '#',
            'producto_id': producto_id,
            'is_physical_gift': bool(producto_id),
        }
        self.save()

    def save(self):
        self.session.modified = True
        if self.user.is_authenticated:
            self._save_to_db()

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            if self.user.is_authenticated and '_db_id' in self.cart[product_id]:
                try:
                    CarritoItem.objects.get(id=self.cart[product_id]['_db_id']).delete()
                except CarritoItem.DoesNotExist:
                    pass
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        valid_items = {k: v for k, v in self.cart.items() if not k.startswith('_') and isinstance(v, dict)}
        product_ids = [int(item['producto_id']) for item in valid_items.values() if not item.get('is_gift') and item.get('producto_id')]
        productos = Producto.objects.filter(id__in=product_ids).prefetch_related('imagenes')
        
        for key, item_data in valid_items.items():
            item = item_data.copy()
            item['cart_key'] = key
            
            if item.get('is_gift'):
                item['producto'] = None
                item['precio_decimal'] = Decimal(item['precio'])
                item['total_precio'] = item['precio_decimal'] * item['quantity']
                item['total'] = item['total_precio']
                yield item
            else:
                producto = next((p for p in productos if p.id == item['producto_id']), None)
                item['producto'] = producto
                
                if 'producto_slug' not in item and producto:
                    item['producto_slug'] = producto.slug
                
                item['precio_decimal'] = Decimal(item['precio'])
                item['total_precio'] = item['precio_decimal'] * item['quantity']
                item['total'] = item['total_precio']
                yield item

    def __len__(self):
        return sum(item['quantity'] for key, item in self.cart.items() if not key.startswith('_') and isinstance(item, dict))

    def get_total_price(self):
        """
        Calcula el precio total de todos los items en el carrito.
        """
        subtotal = sum(
            Decimal(item['precio']) * item['quantity'] 
            for key, item in self.cart.items() 
            if not key.startswith('_') and isinstance(item, dict) and 'precio' in item
        )
        if self.has_gift_wrap():
            subtotal += Decimal('5.00')
        return subtotal

    def clear(self):
        if self.user.is_authenticated:
            CarritoItem.objects.filter(usuario=self.user).delete()
        self.cart = {}
        if settings.CART_SESSION_ID in self.session:
            self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True
        self.save()

    def update_quantity(self, product_id, quantity):
        product_id = str(product_id)
        if product_id in self.cart:
            if quantity > 0:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.remove(product_id)
            self.save()

    def sync_with_stock(self, adjust_to_stock=True):
        # Todo es bajo pedido, no se valida stock
        return

    def set_note(self, note):
        cart_data = self.session.get(settings.CART_SESSION_ID, {})
        cart_data['_note'] = note
        self.session[settings.CART_SESSION_ID] = cart_data
        self.save()

    def get_note(self):
        cart_data = self.session.get(settings.CART_SESSION_ID, {})
        return cart_data.get('_note', '')

    def set_gift_wrap(self, enabled=True):
        cart_data = self.session.get(settings.CART_SESSION_ID, {})
        cart_data['_gift_wrap'] = enabled
        self.session[settings.CART_SESSION_ID] = cart_data
        self.save()

    def has_gift_wrap(self):
        cart_data = self.session.get(settings.CART_SESSION_ID, {})
        return cart_data.get('_gift_wrap', False)
