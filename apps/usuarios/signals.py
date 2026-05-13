"""
Señales (signals) de Django para la app de usuarios.

Se ejecutan automáticamente cuando ocurren ciertos eventos.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario, EmailVerificationToken, NotificacionAdmin
from apps.productos.models import Pedido
from apps.planes.models import SolicitudPlanNovios
from django.urls import reverse
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


@receiver(post_save, sender=Pedido)
def crear_notificacion_pedido(sender, instance, created, **kwargs):
    """Crea una notificación en el admin cuando hay un nuevo pedido"""
    if created:
        try:
            url = reverse('productos:panel_admin_order_detail', args=[instance.id])
        except Exception:
            url = '/panel-admin/pedidos/'
            
        NotificacionAdmin.objects.create(
            tipo='pedido',
            mensaje=f"Nuevo pedido de {instance.nombres} {instance.apellidos}",
            url=url
        )


@receiver(post_save, sender=SolicitudPlanNovios)
def crear_notificacion_plan_novios(sender, instance, created, **kwargs):
    """Crea una notificación en el admin cuando hay una nueva solicitud de plan de novios"""
    if created:
        try:
            url = reverse('planes:panel_admin_solicitudes') + "?estado=pendiente"
        except Exception:
            url = '/panel-admin/solicitudes-novios/'
            
        NotificacionAdmin.objects.create(
            tipo='plan_novios',
            mensaje=f"Nueva solicitud Plan de Novios: {instance.nombres_novios}",
            url=url
        )
