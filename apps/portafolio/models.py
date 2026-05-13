from django.db import models
from django.utils.text import slugify
from apps.productos.utils import compress_image_to_webp
from apps.productos.models import Producto


class Proyecto(models.Model):
    LADO_CHOICES = [
        ('izquierda', 'Imagen a la izquierda'),
        ('derecha', 'Imagen a la derecha'),
    ]

    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='portafolio/')
    lado_imagen = models.CharField(
        max_length=10,
        choices=LADO_CHOICES,
        default='izquierda',
        help_text="¿La imagen va a la izquierda o derecha del texto?"
    )
    etiqueta = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: PROYECTO 1"
    )
    posicion = models.PositiveIntegerField(default=0, help_text="Orden de aparición")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['posicion', 'created_at']
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def save(self, *args, **kwargs):
        if self.imagen and not self.imagen.name.lower().endswith('.webp'):
            self.imagen = compress_image_to_webp(self.imagen)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class ItemLookbook(models.Model):
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lookbook_items'
    )
    # Posición del pin en % sobre la imagen (0-100)
    pos_x = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50,
        help_text="Posición horizontal en % (0=izquierda, 100=derecha)"
    )
    pos_y = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50,
        help_text="Posición vertical en % (0=arriba, 100=abajo)"
    )
    posicion = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['posicion']
        verbose_name = "Item Lookbook"
        verbose_name_plural = "Items Lookbook"

    def __str__(self):
        nombre_prod = self.producto.nombre if self.producto else "Sin producto"
        return f"{self.proyecto.titulo} → {nombre_prod} ({self.pos_x}%, {self.pos_y}%)"