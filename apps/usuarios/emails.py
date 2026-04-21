"""
Utilidades para envío de emails en la app de usuarios.

Nota: Configurar EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, 
      EMAIL_HOST_USER, EMAIL_HOST_PASSWORD en settings.py
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def enviar_email_verificacion(usuario, token):
    """
    Envía email de verificación de cuenta
    """
    asunto = 'Verificar tu cuenta en LivenShop'
    url_verificacion = f"{settings.SITE_URL}/usuarios/verificar-email/{token}/"
    
    contexto = {
        'usuario': usuario,
        'url_verificacion': url_verificacion,
    }
    
    html_message = render_to_string('emails/verificar_email.html', contexto)
    plain_message = f"Por favor verifica tu email en: {url_verificacion}"
    
    send_mail(
        subject=asunto,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=html_message,
        fail_silently=False,
    )


def enviar_codigo_recuperacion(usuario, codigo_reset):
    """
    Envía código de 6 dígitos para recuperar contraseña
    """
    asunto = 'Recuperar tu contraseña en LivenShop'
    
    contexto = {
        'usuario': usuario,
        'codigo': codigo_reset.codigo,
        'tiempo_expira': codigo_reset.tiempo_restante(),
    }
    
    html_message = render_to_string('emails/codigo_recuperacion.html', contexto)
    plain_message = f"Tu código de recuperación es: {codigo_reset.codigo}"
    
    send_mail(
        subject=asunto,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=html_message,
        fail_silently=False,
    )


def enviar_bienvenida(usuario):
    """
    Envía email de bienvenida al usuario registrado
    """
    asunto = f'¡Bienvenido {usuario.get_short_name()} a LivenShop!'
    
    contexto = {
        'usuario': usuario,
    }
    
    html_message = render_to_string('emails/bienvenida.html', contexto)
    plain_message = f"Bienvenido a LivenShop, {usuario.get_full_name()}"
    
    send_mail(
        subject=asunto,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=html_message,
        fail_silently=False,
    )
