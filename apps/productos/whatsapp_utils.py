import logging

logger = logging.getLogger(__name__)

def _build_absolute_url(request, path):
    """Convierte una ruta relativa en URL absoluta cuando hay request."""
    if not path:
        return ''
    return request.build_absolute_uri(path) if request else path

def _get_producto_url(item, request=None):
    """Obtiene una URL estable del producto para incluirla en WhatsApp."""
    if not getattr(item, 'producto', None):
        return ''

    try:
        url_path = item.producto.get_absolute_url()
    except Exception:
        url_path = ''

    return _build_absolute_url(request, url_path)

def generar_mensaje_factura_cliente(pedido, request=None):
    """
    Genera un mensaje estilo FACTURA PROFESIONAL para que el cliente
    lo envíe por WhatsApp a la tienda al finalizar su compra.
    """
    # ── Encabezado ──────────────────────────────────────────────────────────
    mensaje = (
        "*ORDEN DE COMPRA - LIVENSHOP*\n"
        "--------------------------------\n\n"
        f"*Pedido:* #{pedido.id}\n"
        f"*Cliente:* {pedido.nombres} {pedido.apellidos}\n"
        f"*Ciudad:* {pedido.ciudad}, {pedido.pais}\n"
        f"*Telefono:* {pedido.telefono}\n"
    )

    # ── Detalle de productos ─────────────────────────────────────────────────
    mensaje += "\n*DETALLE:*\n"
    for item in pedido.items.all():
        mensaje += f"  - {item.cantidad}x {item.nombre_producto} - ${item.precio:.2f}\n"
        producto_url = _get_producto_url(item, request=request)
        if producto_url:
            mensaje += f"    Ver producto: {producto_url}\n"

    # ── Totales ──────────────────────────────────────────────────────────────
    mensaje += "\n--------------------------------\n"
    if pedido.subtotal:
        mensaje += f"Subtotal: ${pedido.subtotal:.2f}\n"

    mensaje += f"\n*TOTAL A PAGAR: ${pedido.total:.2f}*\n"

    # ── Instrucciones de pago ────────────────────────────────────────────────
    mensaje += (
        "\n*INSTRUCCIONES DE PAGO:*\n"
        "1. Realiza la transferencia al número de cuenta indicado.\n"
        "2. Envía el comprobante a este WhatsApp.\n"
        "3. Tu pedido se procesará al confirmar el pago.\n"
        "\n¡Gracias por comprar en LivenShop!"
    )

    return mensaje

def generar_link_whatsapp_web(numero_destino, mensaje_preview=''):
    """
    Genera un enlace para abrir WhatsApp Web o App con un mensaje predeterminado.
    """
    # Remover caracteres especiales del número
    numero_limpio = numero_destino.replace('+', '').replace(' ', '').replace('-', '')
    
    # Crear URL
    if mensaje_preview:
        from urllib.parse import quote
        mensaje_encoded = quote(mensaje_preview)
        url = f"https://wa.me/{numero_limpio}?text={mensaje_encoded}"
    else:
        url = f"https://wa.me/{numero_limpio}"
    
    return url
