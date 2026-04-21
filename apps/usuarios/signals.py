"""
Señales (signals) de Django para la app de usuarios.

Se ejecutan automáticamente cuando ocurren ciertos eventos.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario, EmailVerificationToken
# from .emails import enviar_email_verificacion, enviar_bienvenida


@receiver(post_save, sender=Usuario)
def crear_token_verificacion(sender, instance, created, **kwargs):
    """
    Crea un token de verificación automáticamente cuando se registra un usuario.
    TODO: Descomentar envío de email cuando esté configurado
    """
    if created and not instance.is_superuser:
        # Crear token
        token = EmailVerificationToken.objects.create(usuario=instance)
        
        # TODO: Enviar email de verificación
        # try:
        #     enviar_email_verificacion(instance, token.token)
        # except Exception as e:
        #     print(f"Error al enviar email de verificación: {e}")
