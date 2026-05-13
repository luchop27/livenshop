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
