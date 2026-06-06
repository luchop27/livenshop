import io
import os
from PIL import Image
from django.core.files.base import ContentFile

def compress_image_to_webp(image_field, max_width=1200, quality=80):
    """
    Optimiza una imagen: la redimensiona si es necesario y la convierte a WebP.
    Retorna un objeto ContentFile listo para ser guardado en un ImageField.
    """
    if not image_field:
        return None

    # Abrir la imagen original
    img = Image.open(image_field)

    # Convertir a RGB (importante para WebP si viene de PNG con transparencia o modo P)
    # Si quieres mantener transparencia, usa WebP con modo RGBA, pero RGB suele pesar menos.
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Redimensionar proporcionalmente si excede el ancho máximo
    if img.width > max_width:
        aspect_ratio = img.height / img.width
        new_height = int(max_width * aspect_ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Guardar en un buffer de memoria como WebP
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=quality, optimize=True)
    buffer.seek(0)

    # Generar el nuevo nombre de archivo con extensión .webp
    original_filename = os.path.basename(image_field.name)
    filename_no_ext = os.path.splitext(original_filename)[0]
    new_filename = f"{filename_no_ext}.webp"

    return ContentFile(buffer.read(), name=new_filename)


def resize_brand_logo_to_webp(image_field, size=(398, 164), padding=20):
    """
    Procesa una imagen de marca para dejarla en formato fijo 398x164px.
    - Mantiene proporción original.
    - No recorta.
    - Centra el logo.
    - Agrega fondo blanco.
    - Convierte a WEBP.
    
    Args:
        image_field: Campo de imagen o archivo a procesar.
        size: Tupla (ancho, alto) del canvas final. Default: (398, 164)
        padding: Padding interno en píxeles. Default: 20
    
    Returns:
        ContentFile con la imagen procesada en formato WEBP.
    """
    if not image_field:
        return None
    
    # Abrir la imagen y convertir a RGBA para mantener transparencia durante el proceso
    img = Image.open(image_field).convert("RGBA")
    
    canvas_w, canvas_h = size
    
    # Calcular el espacio disponible para la imagen
    max_w = canvas_w - padding * 2
    max_h = canvas_h - padding * 2
    
    # Redimensionar manteniendo proporción
    img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    
    # Crear canvas blanco
    canvas = Image.new("RGBA", size, (255, 255, 255, 255))
    
    # Calcular posición para centrar la imagen
    x = (canvas_w - img.width) // 2
    y = (canvas_h - img.height) // 2
    
    # Pegar la imagen en el canvas
    canvas.paste(img, (x, y), img)
    
    # Convertir a RGB y guardar como WEBP
    output = io.BytesIO()
    canvas.convert("RGB").save(output, format="WEBP", quality=95)
    output.seek(0)
    
    # Generar nuevo nombre de archivo
    original_name = os.path.splitext(os.path.basename(image_field.name))[0]
    new_name = f"{original_name}.webp"
    
    return ContentFile(output.getvalue(), name=new_name)
