from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ==================== PROVINCIA ====================
class Provincia(models.Model):
    """Modelo para almacenar las provincias del Ecuador"""
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, blank=True, null=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'
    
    def __str__(self):
        return self.nombre


# ==================== CIUDAD ====================
class Ciudad(models.Model):
    """Modelo para almacenar las ciudades del Ecuador"""
    nombre = models.CharField(max_length=100)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='ciudades'
    )
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        unique_together = ('nombre', 'provincia')
    
    def __str__(self):
        return f"{self.nombre} ({self.provincia.nombre})"


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico')
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_subscribed', False)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin_tienda')
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ('cliente', 'Cliente'),
        ('admin_tienda', 'Administrador de Tienda'),
    ]

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    apellido = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )
    ciudad = models.ForeignKey(
        Ciudad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

    fecha_registro = models.DateTimeField(default=timezone.now)
    fecha_edicion = models.DateTimeField(auto_now=True)

    # Campos de control de Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(
        default=False,
        help_text="Indica si el usuario acepta recibir comunicaciones publicitarias."
    )
    
    # Campo para trackear cupón de carnaval
    carnival_coupon_used_2026 = models.BooleanField(default=False, help_text="Si el usuario ya usó el cupón del 10% de carnaval febrero 2026")
    carnival_coupon_used_date = models.DateTimeField(null=True, blank=True, help_text="Fecha en que usó el cupón de carnaval")

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        if self.nombre and self.apellido:
            return f"{self.nombre} {self.apellido}"
        elif self.nombre:
            return self.nombre
        return self.email

    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.nombre if self.nombre else self.email
    
    def has_carnival_coupon_available(self):
        """Verifica si el usuario tiene el cupón de carnaval disponible (solo febrero 2026)"""
        from datetime import datetime
        now = datetime.now()
        # TEMPORAL: válido en enero y febrero 2026 para pruebas
        if now.year == 2026 and now.month in [1, 2]:
            return not self.carnival_coupon_used_2026
        return False
    
    @property
    def has_used_carnival_coupon(self):
        """Propiedad para templates: verifica si ya usó el cupón"""
        return self.carnival_coupon_used_2026

    def __str__(self):
        return f"{self.email} ({self.rol})"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-fecha_registro']


# ==================== EMAIL VERIFICATION TOKEN ====================
class EmailVerificationToken(models.Model):
    """Token para verificación de email"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.CharField(max_length=100, unique=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Token de verificacion'
        verbose_name_plural = 'Tokens de verificacion'
    
    def __str__(self):
        return f"Token para {self.usuario.email}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            # Generar token único
            import uuid
            self.token = str(uuid.uuid4())
            # Asegurarse de que sea único
            while EmailVerificationToken.objects.filter(token=self.token).exists():
                self.token = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def es_valido(self):
        from datetime import timedelta
        if self.usado:
            return False
        horas = 48
        return timezone.now() <= self.creado + timedelta(hours=horas)
    
    @staticmethod
    def generar_token():
        import uuid
        return str(uuid.uuid4())


# ==================== PASSWORD RESET CODE ====================
class PasswordResetCode(models.Model):
    """Código de 6 dígitos numéricos para recuperar contraseña"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reset_codes')
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    expira_en = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Código de recuperación'
        verbose_name_plural = 'Códigos de recuperación'
        ordering = ['-creado']
    
    def __str__(self):
        return f"Código {self.codigo} para {self.usuario.email}"
    
    def save(self, *args, **kwargs):
        if not self.expira_en:
            from datetime import timedelta
            # El código expira en 15 minutos
            self.expira_en = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generar_codigo():
        """Genera un código numérico de 6 dígitos único"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def es_valido(self):
        """Verifica si el código sigue siendo válido"""
        if self.usado:
            return False
        if not self.expira_en:
            return False
        return timezone.now() <= self.expira_en
    
    def tiempo_restante(self):
        """Retorna el tiempo restante en segundos"""
        if not self.es_valido():
            return 0
        delta = self.expira_en - timezone.now()
        return max(0, int(delta.total_seconds()))


# ==================== WISHLIST ====================
class Wishlist(models.Model):
    """Modelo para guardar productos favoritos del usuario"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='wishlist')
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, related_name='en_wishlist')
    agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'producto')
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-agregado']
    
    def __str__(self):
        return f"{self.usuario.email} - {self.producto.nombre}"
