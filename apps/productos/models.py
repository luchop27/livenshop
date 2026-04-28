# apps/productos/models.py
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import os


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
    if ext not in valid_extensions:
        raise ValidationError(f'Archivo no permitido. Solo se aceptan: {", ".join(valid_extensions)}')


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.heic', '.heif']
    if ext not in valid_extensions:
        raise ValidationError(f'Archivo no permitido. Solo se aceptan: {", ".join(valid_extensions)}')


def generate_unique_slug(model_class, value, instance_pk=None):
    """Genera un slug único para un modelo dado."""
    base_slug = slugify(value)
    slug = base_slug
    counter = 1

    while True:
        queryset = model_class.objects.filter(slug=slug)
        if instance_pk:
            queryset = queryset.exclude(pk=instance_pk)
        if not queryset.exists():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


# -----------------------------
# MARCA
# -----------------------------
class Marca(models.Model):
    """
    Marca comercial asociada a productos del catálogo.
    """
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    imagen = models.ImageField(upload_to='marcas/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(Marca, self.nombre, self.pk)
        super().save(*args, **kwargs)


# -----------------------------
# COLECCIÓN
# -----------------------------
class Coleccion(models.Model):
    """
    Agrupa categorías bajo un tema o temporada.
    Ejemplo: "Otoño 2024", "Estilo Nórdico", "Minimalismo"
    """
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(
        upload_to='colecciones/',
        blank=True,
        null=True,
        help_text="Imagen representativa de la colección"
    )
    activo = models.BooleanField(default=True)
    destacada = models.BooleanField(default=False, help_text="Mostrar en página principal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Colección"
        verbose_name_plural = "Colecciones"

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('productos:lista_por_coleccion', args=[self.slug])


# -----------------------------
# CATEGORÍA
# -----------------------------
class Categoria(models.Model):
    """
    Categoría y subcategoría de productos.
    Soporta jerarquía: padre -> subcategorías.
    Ejemplo: Decor -> Cuadros, Jarrones, Espejos
    El menú del nav se construye desde aquí dinámicamente.
    """
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(
        upload_to='categorias/',
        blank=True,
        null=True,
        help_text="Imagen representativa de la categoría"
    )
    coleccion = models.ForeignKey(
        Coleccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categorias',
        help_text="Colección a la que pertenece esta categoría (opcional)"
    )
    padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategorias',
        help_text="Déjalo vacío si es una categoría principal"
    )
    posicion = models.PositiveIntegerField(
        default=0,
        help_text="Orden de aparición en el menú"
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['posicion', 'nombre']
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        if self.padre:
            return f"{self.padre.nombre} → {self.nombre}"
        return self.nombre

    def get_absolute_url(self):
        return reverse('productos:lista_por_categoria', args=[self.slug])

    def es_principal(self):
        return self.padre is None


# -----------------------------
# PRODUCTO
# -----------------------------
class Producto(models.Model):
    """
    Producto de decoración del hogar.
    Stock y precio directamente en el producto (sin variantes).
    """
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )
    marca = models.ForeignKey(
        Marca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        help_text='Marca comercial asociada a este producto'
    )
    coleccion = models.ForeignKey(
        Coleccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos',
        help_text="Colección a la que pertenece este producto (opcional)"
    )

    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    descripcion_corta = models.TextField(blank=True, null=True)
    descripcion_completa = models.TextField(blank=True, null=True)

    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    precio_oferta = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Si tiene precio de oferta, ingrésalo aquí"
    )
    stock = models.PositiveIntegerField(default=0)
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Peso del producto en kg'
    )

    # Dimensiones/medidas (útil para decoración)
    dimensiones = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Ej: 30cm x 20cm x 10cm"
    )
    material = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Ej: Cerámica, Madera, Vidrio"
    )

    destacado = models.BooleanField(default=False, help_text="Mostrar en página principal")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        try:
            return reverse('productos:detalle_producto', args=[self.slug])
        except Exception:
            return f"/producto/{self.slug}/"

    def tiene_stock(self):
        return self.stock > 0

    def tiene_oferta(self):
        return self.precio_oferta is not None and self.precio_oferta < self.precio

    def precio_final(self):
        if self.tiene_oferta():
            return self.precio_oferta
        return self.precio

    def porcentaje_descuento(self):
        if self.tiene_oferta() and self.precio:
            descuento = ((self.precio - self.precio_oferta) / self.precio) * 100
            return round(descuento)
        return 0


# -----------------------------
# IMAGEN / VIDEO
# -----------------------------
class Imagen(models.Model):
    """
    Imagen o video asociado a un producto.
    """
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('video', 'Video'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='imagenes'
    )
    tipo_medio = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='imagen'
    )
    imagen = models.ImageField(
        upload_to='productos/imagenes/',
        blank=True,
        null=True,
        validators=[validate_image_extension],
        help_text="JPG, PNG, GIF, WebP, HEIC"
    )
    video = models.FileField(
        upload_to='productos/videos/',
        blank=True,
        null=True,
        validators=[validate_video_extension],
        help_text="MP4, WebM, MOV"
    )
    url = models.TextField(
        default='',
        blank=True,
        help_text="URL alternativa si no se sube archivo"
    )
    posicion = models.PositiveIntegerField(default=0, help_text="Orden de visualización")
    es_principal = models.BooleanField(default=False, help_text="Imagen principal del producto")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-es_principal', 'posicion', 'created_at']
        verbose_name = "Imagen/Video"
        verbose_name_plural = "Imágenes/Videos"

    def __str__(self):
        tipo = "Video" if self.tipo_medio == 'video' else "Imagen"
        return f"{tipo} de {self.producto.nombre}"

    def clean(self):
        super().clean()
        if self.tipo_medio == 'video':
            if self.imagen and not self.video:
                raise ValidationError({
                    'tipo_medio': 'Seleccionaste "Video" pero subiste una imagen.'
                })
            if not self.video and not self.url:
                raise ValidationError({'video': 'Sube un archivo de video o proporciona una URL.'})
        elif self.tipo_medio == 'imagen':
            if self.video and not self.imagen:
                raise ValidationError({
                    'tipo_medio': 'Seleccionaste "Imagen" pero subiste un video.'
                })
            if not self.imagen and not self.url:
                raise ValidationError({'imagen': 'Sube una imagen o proporciona una URL.'})

    @property
    def src(self):
        if self.tipo_medio == 'video' and self.video:
            return self.video.url
        if self.imagen:
            return self.imagen.url
        return self.url or ""

    @property
    def es_video(self):
        return self.tipo_medio == 'video'


# -----------------------------
# ATRIBUTO (genérico y flexible)
# -----------------------------
class Atributo(models.Model):
    """
    Atributos personalizables por producto.
    Para decoración: Material, Dimensiones, País de origen, Peso, etc.
    """
    nombre = models.CharField(max_length=100, help_text="Ej: Material, País de origen, Peso")
    slug = models.SlugField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)
    posicion = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['posicion', 'nombre']
        verbose_name = "Atributo"
        verbose_name_plural = "Atributos"

    def __str__(self):
        return self.nombre


class AtributoProducto(models.Model):
    """
    Valor de un atributo para un producto específico.
    Ejemplo: Producto "Jarrón Nórdico" -> Material: Cerámica
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='atributos'
    )
    atributo = models.ForeignKey(
        Atributo,
        on_delete=models.CASCADE,
        related_name='valores_producto'
    )
    valor = models.CharField(max_length=200, help_text="Ej: Cerámica, Hecho a mano, México")

    class Meta:
        verbose_name = "Atributo del Producto"
        verbose_name_plural = "Atributos del Producto"
        unique_together = [['producto', 'atributo']]
        ordering = ['atributo__posicion']

    def __str__(self):
        return f"{self.producto.nombre} — {self.atributo.nombre}: {self.valor}"


# -----------------------------
# CARRITO
# -----------------------------
class CarritoItem(models.Model):
    """
    Item del carrito de compras persistente por usuario.
    """
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='carrito_items'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen_url = models.URLField(blank=True, null=True)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_agregado']
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"
        unique_together = ('usuario', 'producto')

    def __str__(self):
        return f"{self.usuario.email} — {self.producto.nombre} x{self.cantidad}"

    @property
    def total_precio(self):
        return self.precio * self.cantidad


# -----------------------------
# INFORMACIÓN DE ENVÍO
# -----------------------------
class ShippingInfo(models.Model):
    titulo = models.CharField(max_length=200, default="Shipping & Delivery")
    descripcion = models.TextField(help_text="Descripción general de la política de envío")
    tiempo_nacional = models.CharField(max_length=100, blank=True, help_text="Ej: 3-6 días")
    tiempo_internacional = models.CharField(max_length=100, blank=True, help_text="Ej: 12-26 días")
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    envio_gratis_desde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monto mínimo para envío gratis"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Información de Envío"
        verbose_name_plural = "Información de Envío"

    def __str__(self):
        return self.titulo


# -----------------------------
# POLÍTICA DE DEVOLUCIÓN
# -----------------------------
class ReturnPolicy(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, blank=True, help_text="Clase CSS del ícono (opcional)")
    dias_devolucion = models.PositiveIntegerField(default=30)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden']
        verbose_name = "Política de Devolución"
        verbose_name_plural = "Políticas de Devolución"

    def __str__(self):
        return self.titulo


class ShopGramPost(models.Model):
    instagram_url = models.URLField(verbose_name="URL de Instagram")
    imagen = models.ImageField(upload_to='shopgram/', verbose_name="Imagen", blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Shop Gram Post"
        verbose_name_plural = "Shop Gram Posts"

    def __str__(self):
        return self.instagram_url