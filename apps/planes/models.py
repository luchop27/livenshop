from django.db import models

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