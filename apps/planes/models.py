from django.db import models
from apps.productos.utils import compress_image_to_webp


class Plan(models.Model):
    TIPO_CHOICES = [
        ('novios', 'Plan Novios'),
        ('eventos', 'Plan Eventos'),
        ('decoradores', 'Inscripción Decoradores'),
        ('restaurantes', 'Restaurantes'),
        ('casa_nueva', 'Casa Nueva'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, unique=True)
    nombre = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    # Secciones de contenido (editables desde el admin)
    titulo_terminos = models.CharField(max_length=200, default='Términos')
    contenido_terminos = models.TextField(blank=True)

    titulo_beneficios = models.CharField(max_length=200, default='Beneficios')
    contenido_beneficios = models.TextField(blank=True)

    # Botones (opcionales según el plan)
    texto_boton_principal = models.CharField(max_length=100, blank=True)
    url_boton_principal = models.CharField(max_length=200, blank=True)

    texto_boton_secundario = models.CharField(max_length=100, blank=True)
    url_boton_secundario = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'

    def __str__(self):
        return self.nombre


class SeccionPlan(models.Model):
    """Secciones adicionales de contenido para cada plan."""
    plan = models.ForeignKey(Plan, related_name='secciones', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = 'Sección del Plan'
        verbose_name_plural = 'Secciones del Plan'

    def __str__(self):
        return f"{self.plan.nombre} — {self.titulo}"


# ══════════════════════════════════════════════════════
# ALIADOS / BENEFICIOS PLAN NOVIOS
# ══════════════════════════════════════════════════════

class AliadoBeneficio(models.Model):
    """Marca aliada que ofrece beneficios exclusivos al Plan de Novios."""

    CATEGORIA_CHOICES = [
        ('hoteles', 'Hoteles'),
        ('eventos_flores', 'Eventos y Flores'),
        ('fotografia', 'Fotografía'),
        ('bakery', 'Bakery / Pastelería'),
        ('spa_belleza', 'Spa & Belleza'),
        ('viajes', 'Viajes'),
        ('musica', 'Música / DJ'),
        ('vestimenta', 'Vestimenta & Moda'),
        ('decoracion', 'Decoración'),
        ('gastronomia', 'Gastronomía / Bar'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=150, verbose_name='Nombre de la marca')
    logo = models.ImageField(
        upload_to='aliados/',
        blank=True, null=True,
        verbose_name='Logo (se procesará a fondo blanco)'
    )
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        default='otro',
        verbose_name='Categoría'
    )
    descripcion_beneficio = models.TextField(
        verbose_name='Descripción del beneficio',
        help_text='Ej: 10% de descuento en todos los servicios...'
    )
    email = models.EmailField(blank=True, null=True, verbose_name='Email de contacto')
    telefono = models.CharField(max_length=30, blank=True, null=True, verbose_name='Teléfono')
    instagram = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Instagram (sin @)',
        help_text='Solo el nombre de usuario, ej: liven.home.decor'
    )
    sitio_web = models.URLField(blank=True, null=True, verbose_name='Sitio web')
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Aliado / Beneficio'
        verbose_name_plural = 'Aliados / Beneficios'

    def save(self, *args, **kwargs):
        if self.logo and not self.logo.name.lower().endswith('.webp'):
            self.logo = compress_image_to_webp(self.logo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


# ══════════════════════════════════════════════════════
# PLAN NOVIOS — SALDO DE NOVIOS (Portal 24/7)
# ══════════════════════════════════════════════════════

class PlanNovios(models.Model):
    """Registro de una pareja en el Plan de Novios."""
    nombres = models.CharField(max_length=200, verbose_name='Nombre(s) de los novios')
    email = models.EmailField(unique=True, verbose_name='Email de acceso')
    clave = models.CharField(max_length=128, verbose_name='Clave de acceso (hash)')
    fecha_boda = models.DateField(blank=True, null=True, verbose_name='Fecha de la boda')
    saldo_acumulado = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Saldo acumulado ($)'
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan de Novios'
        verbose_name_plural = 'Planes de Novios'

    def __str__(self):
        return f"{self.nombres} — ${self.saldo_acumulado}"


class MovimientoPlan(models.Model):
    """Registro de aportes y movimientos del plan de novios."""
    TIPO_CHOICES = [
        ('aporte', 'Aporte'),
        ('anticipo', 'Anticipo'),
        ('devolucion', 'Devolución'),
        ('ajuste', 'Ajuste'),
    ]
    plan = models.ForeignKey('SolicitudPlanNovios', related_name='movimientos', on_delete=models.CASCADE)
    producto = models.ForeignKey('productos.Producto', null=True, blank=True, on_delete=models.SET_NULL, related_name='movimientos_plan', help_text="Si es un abono a un producto específico")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='aporte')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=250, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'

    def __str__(self):
        return f"{self.plan.nombres_novios} — {self.tipo} ${self.monto}"


class SolicitudPlanNovios(models.Model):
    """Solicitudes enviadas desde el formulario de la landing page."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('finalizado', 'Finalizado'),
    ]

    nombres_novios = models.CharField(max_length=255, verbose_name='Nombres de los Novios')
    email = models.EmailField(verbose_name='Email de contacto')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono / WhatsApp')
    fecha_boda = models.DateField(verbose_name='Fecha tentativa de boda')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    mensaje = models.TextField(blank=True, verbose_name='Comentario adicional')
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado',
        help_text='Solo los planes "Aprobados" aparecen en la lista pública.'
    )
    productos_regalo = models.ManyToManyField(
        'productos.Producto', 
        blank=True, 
        verbose_name='Productos elegidos como regalo'
    )
    foto_pareja = models.ImageField(
        upload_to='planes/parejas/',
        blank=True, null=True,
        verbose_name='Foto de la Pareja',
        help_text='Foto que se mostrará en la página para dejar regalos (en lugar de la tarjeta azul por defecto)'
    )
    clave = models.CharField(max_length=128, blank=True, verbose_name='Clave Portal (Hash)')
    saldo_acumulado = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Saldo Acumulado ($)')
    procesado = models.BooleanField(default=False, verbose_name='¿Ya se contactó?')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Solicitud de Plan'
        verbose_name_plural = 'Solicitudes de Planes'
        ordering = ['-fecha_solicitud']

    def save(self, *args, **kwargs):
        if self.foto_pareja and not self.foto_pareja.name.lower().endswith('.webp'):
            self.foto_pareja = compress_image_to_webp(self.foto_pareja)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombres_novios} — {self.get_estado_display()} — {self.fecha_solicitud.strftime('%d/%m/%Y')}"
