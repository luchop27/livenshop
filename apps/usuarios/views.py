from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .models import Usuario, EmailVerificationToken, Provincia, Ciudad, Wishlist, PasswordResetCode, NotificacionAdmin
from apps.productos.models import Producto
import base64
import os

# Limpiar variables de entorno de CA Bundle rotas de PostgreSQL en Windows para que requests funcione con SSL
for var in ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"]:
    if var in os.environ and "PostgreSQL" in os.environ[var] and not os.path.exists(os.environ[var]):
        del os.environ[var]


def limpiar_mensajes_pendientes(request):
    """Consume mensajes pendientes para evitar arrastre entre panel admin y frontend."""
    storage = get_messages(request)
    storage.used = True


def obtener_logo_url(request):
    """Obtiene la URL absoluta del logo de la tienda"""
    if request:
        # En producción o local, build_absolute_uri crea la URL absoluta completa (ej: https://liven.ec/static/images/logo/1logolivenblanco.png)
        return request.build_absolute_uri('/static/images/logo/1logolivenblanco.png')
    return "https://livenshop-media.s3.amazonaws.com/static/images/logo/1logolivenblanco.png"


def enviar_email_directo(destinatario, asunto, mensaje_html):
    """
    Envía emails usando primero Resend API, con reintento opcional si es sandbox,
    y fallback al sistema nativo de Django (SMTP/SES).
    """
    import json
    import requests
    
    # 1. Intentar con Resend API primero
    resend_key = getattr(settings, 'RESEND_API_KEY', None)
    if resend_key:
        print(f"🔌 Intentando envío vía Resend API a {destinatario}...")
        url = "https://api.resend.com/emails"
        
        # Primero intentamos con el remitente por defecto de la tienda
        sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'hola@liven.ec')
        
        headers = {
            'Authorization': f'Bearer {resend_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "from": f"LivenShop <{sender_email}>",
            "to": [destinatario],
            "subject": asunto,
            "html": mensaje_html
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code >= 200 and response.status_code < 300:
                print(f"✅ Email enviado exitosamente vía Resend a {destinatario}")
                return True, ""
            else:
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {}
                
                print(f"⚠️ Resend devolvió error {response.status_code}: {response.text}")
                
                # Si es un error de dominio no verificado o prohibido, reintentamos con onboarding@resend.dev (Sandbox)
                error_msg = error_data.get('message', '').lower() if error_data else response.text.lower()
                is_unauthorized_domain = any(x in error_msg for x in ["domain", "verify", "unauthorized", "restrict"]) or response.status_code in [403, 422]
                
                if is_unauthorized_domain:
                    print("🔄 Reintentando con remitente de onboarding (sandbox)...")
                    payload["from"] = "LivenShop <onboarding@resend.dev>"
                    retry_response = requests.post(url, headers=headers, json=payload, timeout=10)
                    if retry_response.status_code >= 200 and retry_response.status_code < 300:
                        print(f"✅ Email enviado exitosamente vía Resend Sandbox a {destinatario}")
                        return True, ""
                    else:
                        print(f"❌ Falló reintento con onboarding: {retry_response.text}")
        except Exception as re_e:
            print(f"❌ Error conectando a la API de Resend: {re_e}")

    # 2. Fallback: Intentar con SMTP de Django (Configurado para Amazon SES)
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags
    
    try:
        print(f"🚀 Fallback: Intentando envío vía SMTP/SES a {destinatario}...")
        sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'hola@liven.ec')
        text_content = strip_tags(mensaje_html)
        
        email = EmailMultiAlternatives(
            asunto,
            text_content,
            f"LivenShop <{sender_email}>",
            [destinatario]
        )
        email.attach_alternative(mensaje_html, "text/html")
        
        # Enviar
        email.send(fail_silently=False)
        print(f"✅ Email enviado exitosamente vía SMTP a {destinatario}")
        return True, ""
        
    except Exception as e:
        print(f"❌ Error final en envío SMTP: {str(e)}")
        return False, f"Resend API y SMTP/SES fallaron. Último error: {str(e)}"


def enviar_email_verificacion(request, usuario):
    """Envía el correo de verificación de email"""
    try:
        token_obj = EmailVerificationToken.objects.create(usuario=usuario)
        
        verify_url = request.build_absolute_uri(
            f'/usuarios/verificar-email/{token_obj.token}/'
        )
        
        logo_src = "cid:logoselena"
        nombre_usuario = usuario.nombre or usuario.email.split('@')[0]
        
        mensaje_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 40px rgba(145, 133, 103, 0.15);
                }}
                .header {{
                    background: linear-gradient(135deg, #918567 0%, #a89878 100%);
                    padding: 50px 30px;
                    text-align: center;
                }}
                .logo-container {{
                    text-align: center;
                    margin-bottom: 25px;
                }}
                .logo {{
                    max-width: 150px;
                    height: auto;
                    background: white;
                    padding: 15px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .header-title {{
                    color: white;
                    margin: 0;
                    font-size: 32px;
                    font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header-subtitle {{
                    color: rgba(255,255,255,0.95);
                    margin: 10px 0 0;
                    font-size: 16px;
                }}
                .content {{
                    padding: 50px 40px;
                }}
                .greeting {{
                    font-size: 22px;
                    color: #333;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                .message {{
                    color: #555;
                    line-height: 1.8;
                    margin-bottom: 30px;
                    font-size: 16px;
                }}
                .btn-container {{
                    text-align: center;
                    margin: 40px 0;
                }}
                .btn {{
                    display: inline-block;
                    background: linear-gradient(135deg, #918567 0%, #a89878 100%);
                    color: white !important;
                    padding: 18px 50px;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 8px 20px rgba(145, 133, 103, 0.3);
                    transition: all 0.3s ease;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 12px 24px rgba(145, 133, 103, 0.4);
                }}
                .features {{
                    background: linear-gradient(to bottom, #faf9f7, #ffffff);
                    border: 2px solid #f0ebe3;
                    padding: 30px;
                    border-radius: 12px;
                    margin: 30px 0;
                }}
                .features h3 {{
                    color: #918567;
                    margin: 0 0 20px;
                    font-size: 18px;
                }}
                .feature-item {{
                    display: flex;
                    align-items: center;
                    margin: 15px 0;
                }}
                .feature-icon {{
                    font-size: 24px;
                    margin-right: 15px;
                    min-width: 30px;
                }}
                .feature-text {{
                    color: #666;
                    font-size: 15px;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(to right, transparent, #d4cfc4, transparent);
                    margin: 30px 0;
                }}
                .footer {{
                    background: linear-gradient(to bottom, #faf9f7, #f5f3f0);
                    padding: 30px;
                    text-align: center;
                    border-top: 2px solid #e8e3da;
                }}
                .footer-text {{
                    color: #999;
                    font-size: 13px;
                    margin: 5px 0;
                }}
                .footer-text a {{
                    color: #918567;
                    text-decoration: none;
                }}
                .link-alternative {{
                    margin-top: 20px;
                    padding: 15px;
                    background: #faf9f7;
                    border: 1px solid #e8e3da;
                    border-radius: 8px;
                    word-break: break-all;
                }}
                .link-alternative p {{
                    color: #888;
                    font-size: 12px;
                    margin: 0 0 10px;
                }}
                .link-alternative a {{
                    color: #918567;
                    font-size: 13px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo-container">
                        <img src="{logo_src}" alt="LivenShop" class="logo">
                    </div>
                    <h1 class="header-title">🎉 ¡Bienvenido!</h1>
                    <p class="header-subtitle">Tu cuenta ha sido creada exitosamente</p>
                </div>
                
                <div class="content">
                    <p class="greeting">Hola <strong>{nombre_usuario}</strong>,</p>
                    
                    <p class="message">
                        ¡Gracias por unirte a <strong>LivenShop</strong>! Estamos emocionados de tenerte como parte de nuestra comunidad. 
                        Para completar tu registro y desbloquear todas las funciones, por favor verifica tu dirección de correo electrónico.
                    </p>
                    
                    <div class="btn-container">
                        <a href="{verify_url}" class="btn">
                            ✨ Verificar mi Email
                        </a>
                    </div>
                    
                    <div class="features">
                        <h3>🌟 Beneficios de tu cuenta verificada:</h3>
                        <div class="feature-item">
                            <span class="feature-icon">🛍️</span>
                            <span class="feature-text">Acceso completo a nuestro catálogo exclusivo</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">📦</span>
                            <span class="feature-text">Seguimiento de pedidos en tiempo real</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">🎁</span>
                            <span class="feature-text">Ofertas exclusivas y descuentos especiales</span>
                        </div>
                        <div class="feature-item">
                            <span class="feature-icon">💳</span>
                            <span class="feature-text">Proceso de compra rápido y seguro</span>
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div class="link-alternative">
                        <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                        <a href="{verify_url}">{verify_url}</a>
                    </div>
                    
                    <p style="color: #999; font-size: 13px; margin-top: 30px; text-align: center;">
                        Este enlace expira en 48 horas.
                    </p>
                </div>
                
                <div class="footer">
                    <p class="footer-text">Este correo fue enviado automáticamente. Por favor no respondas.</p>
                    <p class="footer-text">© 2026 LivenShop - Todos los derechos reservados</p>
                    <p class="footer-text" style="margin-top: 15px;">
                        ¿Necesitas ayuda? <a href="mailto:soporte@livenshop.com">Contáctanos</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        asunto = '🎉 ¡Bienvenido a LivenShop! Verifica tu email'
        return enviar_email_directo(usuario.email, asunto, mensaje_html)
        
    except Exception as e:
        print(f"Error en enviar_email_verificacion: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def enviar_email_codigo_recuperacion(request, usuario, codigo):
    """Envía el email con el código de 6 dígitos para recuperación de contraseña"""
    try:
        logo_src = obtener_logo_url(request)
        nombre_usuario = usuario.nombre or usuario.email.split('@')[0]
        
        mensaje_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recupera tu Contraseña</title>
            <style>
                body {{
                    font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #f7f9fc;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .wrapper {{
                    width: 100%;
                    background-color: #f7f9fc;
                    padding: 40px 0;
                }}
                .container {{
                    max-width: 580px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(12, 32, 56, 0.05);
                }}
                .header {{
                    background: linear-gradient(135deg, #0C2038 0%, #153254 100%);
                    padding: 40px 20px;
                    text-align: center;
                }}
                .logo {{
                    max-height: 50px;
                    width: auto;
                }}
                .content {{
                    padding: 40px 35px;
                    color: #334155;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #0C2038;
                    margin-top: 0;
                    margin-bottom: 15px;
                    text-align: center;
                }}
                .greeting {{
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 25px;
                }}
                .code-box {{
                    background-color: #f8fafc;
                    border: 2px dashed #C9A96E;
                    border-radius: 12px;
                    padding: 24px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .code-title {{
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    color: #64748b;
                    margin-bottom: 10px;
                    font-weight: 600;
                }}
                .code-number {{
                    font-size: 38px;
                    font-weight: 800;
                    color: #C9A96E;
                    letter-spacing: 6px;
                    margin: 0;
                    font-family: 'Courier New', Courier, monospace;
                }}
                .info-text {{
                    font-size: 14px;
                    line-height: 1.6;
                    color: #64748b;
                    margin-bottom: 20px;
                }}
                .divider {{
                    height: 1px;
                    background-color: #e2e8f0;
                    margin: 30px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 30px 20px;
                    background-color: #f8fafc;
                    border-top: 1px solid #f1f5f9;
                }}
                .footer-text {{
                    font-size: 12px;
                    color: #94a3b8;
                    line-height: 1.5;
                    margin: 5px 0;
                }}
                .footer-link {{
                    color: #C9A96E;
                    text-decoration: none;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <div class="container">
                    <div class="header">
                        <img src="{logo_src}" alt="Liven" class="logo">
                    </div>
                    <div class="content">
                        <h2 class="title">Recuperación de Contraseña</h2>
                        <p class="greeting">Hola, <strong>{nombre_usuario}</strong>:</p>
                        <p class="greeting">Recibimos una solicitud para restablecer la contraseña de tu cuenta en <strong>Liven</strong>. Para continuar con el proceso, utiliza el siguiente código de verificación de 6 dígitos:</p>
                        
                        <div class="code-box">
                            <div class="code-title">Código de Verificación</div>
                            <div class="code-number">{codigo}</div>
                        </div>
                        
                        <p class="info-text" style="text-align: center;">
                            Este código es válido por <strong>15 minutos</strong>.<br>
                            Si tú no realizaste esta solicitud, puedes ignorar este correo de forma segura; tu contraseña seguirá siendo la misma.
                        </p>
                        
                        <div class="divider"></div>
                        
                        <p class="info-text" style="font-size: 12px; text-align: center;">
                            Por motivos de seguridad, nunca compartas este código con nadie. El equipo de Liven nunca te pedirá tus credenciales ni códigos por correo ni llamada.
                        </p>
                    </div>
                    <div class="footer">
                        <p class="footer-text">© 2026 Liven — Boutique de Regalos & Decoración</p>
                        <p class="footer-text">¿Necesitas ayuda? <a href="https://wa.me/593989387657" class="footer-link">Contáctanos por WhatsApp</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        asunto = f'🔐 {codigo} es tu código de recuperación - LivenShop'
        return enviar_email_directo(usuario.email, asunto, mensaje_html)
    except Exception as e:
        print(f"Error enviando código: {e}")
        return False, str(e)



def login_usuario(request):
    """Vista de login para usuarios"""
    limpiar_mensajes_pendientes(request)

    if request.user.is_authenticated:
        if request.user.rol == 'admin_tienda' or request.user.is_staff:
            return redirect('panel_admin_demo')
        return redirect('usuarios:my_account')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url == 'None':
            next_url = None

        if not email or not password:
            messages.error(request, 'Por favor, ingrese email y contraseña.')
            return render(request, 'login.html', {'next': next_url, 'disable_cart_nav': True})

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            
            # Prioridad de redirección: next -> admin/staff -> my-account
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            
            if user.rol == 'admin_tienda' or user.is_staff:
                return redirect('panel_admin_demo')
            
            return redirect('usuarios:my_account')
        else:
            messages.error(request, 'Email o contraseña incorrectos.')
            return render(request, 'login.html', {
                'next': next_url,
                'disable_cart_nav': True,
            })
    
    next_url = request.GET.get('next')
    return render(request, 'login.html', {
        'next': next_url,
        'disable_cart_nav': True,
    })



def registrar_usuario(request):
    """Vista de registro para nuevos clientes"""
    if request.user.is_authenticated:
        return redirect('usuarios:my_account')

    def construir_contexto_registro(**kwargs):
        """Construye el contexto base del registro y preserva datos del formulario."""
        provincia_id_ctx = kwargs.get('provincia_id')
        contexto = {
            'disable_cart_nav': True,
            'provincias': obtener_provincias(),
            'ciudades': obtener_ciudades_por_provincia(provincia_id_ctx) if provincia_id_ctx else []
        }
        contexto.update(kwargs)
        return contexto
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        provincia_nombre = request.POST.get('provincia')
        ciudad_nombre = request.POST.get('ciudad')
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        if not provincia_nombre or not ciudad_nombre:
            messages.error(request, 'Debes seleccionar una provincia y una ciudad/cantón.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_nombre,
                ciudad_id=ciudad_nombre,
            ))
        
        if not email or not password:
            messages.error(request, 'El email y la contraseña son obligatorios.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_nombre,
                ciudad_id=ciudad_nombre,
            ))
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_nombre,
                ciudad_id=ciudad_nombre,
            ))
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_nombre,
                ciudad_id=ciudad_nombre,
            ))
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_nombre,
                ciudad_id=ciudad_nombre,
            ))
        
        try:
            provincia = None
            ciudad = None
            
            if provincia_nombre:
                provincia, _ = Provincia.objects.get_or_create(nombre=provincia_nombre, defaults={'activa': True})

            if not provincia:
                messages.error(request, 'La provincia seleccionada no es válida.')
                return render(request, 'register.html', construir_contexto_registro(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono,
                    provincia_id=provincia_nombre,
                    ciudad_id=ciudad_nombre,
                ))
            
            if ciudad_nombre:
                ciudad, _ = Ciudad.objects.get_or_create(nombre=ciudad_nombre, provincia=provincia, defaults={'activa': True})

            if not ciudad:
                messages.error(request, 'La ciudad/cantón seleccionada no pertenece a la provincia elegida.')
                return render(request, 'register.html', construir_contexto_registro(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono,
                    provincia_id=provincia_nombre,
                    ciudad_id=ciudad_nombre,
                ))
            
            user = Usuario.objects.create_user(
                email=email,
                password=password,
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                provincia=provincia,
                ciudad=ciudad,
                rol='cliente',
                is_active=True,
            )

            messages.success(
                request,
                '¡Registro exitoso! Por favor, inicia sesión con tus credenciales'
            )
            return redirect('usuarios:login')
            
        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
    
    return render(request, 'register.html', construir_contexto_registro())


def obtener_provincias():
    """Helper para obtener todas las provincias activas"""
    return Provincia.objects.filter(activa=True).order_by('nombre')


def obtener_ciudades_por_provincia(provincia_id):
    """Helper para obtener ciudades de una provincia específica"""
    if provincia_id:
        try:
            return Ciudad.objects.filter(provincia_id=provincia_id, activa=True).order_by('nombre')
        except:
            return []
    return []


def logout_usuario(request):
    """Vista de logout para usuarios"""
    limpiar_mensajes_pendientes(request)
    logout(request)
    limpiar_mensajes_pendientes(request)
    return redirect('usuarios:login')


@login_required(login_url='/')
def my_account(request):
    """Dashboard principal de la cuenta del usuario"""
    return render(request, 'my-account.html', {
        'user': request.user
    })


@login_required(login_url='/')
def my_account_orders(request):
    """Historial de órdenes del usuario"""
    from apps.productos.models import Pedido
    ordenes = Pedido.objects.filter(usuario=request.user).order_by('-created_at')

    from django.core.paginator import Paginator
    paginator = Paginator(ordenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'my-account-orders.html', {
        'user': request.user,
        'ordenes': page_obj,
    })


@login_required(login_url='/')
def my_account_orders_details(request, pedido_id):
    """Detalles de un pedido específico con enlace opcional de WhatsApp."""
    from apps.productos.models import Pedido
    from urllib.parse import quote

    orden = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)

    whatsapp_url = ''
    try:
        items_txt = ''
        for item in orden.items.all():
            costo = item.precio * item.cantidad
            items_txt += f'\n  • {item.nombre_producto} x{item.cantidad} — ${costo}'
        msg = (
            f'Hola, quiero consultar mi pedido *#{orden.id}*\n'
            f'Fecha: {orden.created_at.strftime("%d/%m/%Y")}\n'
            f'Estado: {orden.get_estado_display()}\n'
            f'Productos:{items_txt}\n'
            f'Total: *${orden.total}*'
        )
        # Intentar obtener número desde configuración de la tienda
        try:
            from apps.ayudas.models import DatosContacto
            contacto = DatosContacto.objects.first()
            numero = contacto.whatsapp_pedidos if (contacto and hasattr(contacto, 'whatsapp_pedidos')) else ''
        except Exception:
            numero = ''
        numero_limpio = numero.replace('+', '').replace(' ', '').replace('-', '') if numero else ''
        if numero_limpio:
            whatsapp_url = f'https://wa.me/{numero_limpio}?text={quote(msg, encoding="utf-8")}'
    except Exception:
        pass

    return render(request, 'my-account-orders-details.html', {
        'user': request.user,
        'orden': orden,
        'whatsapp_url': whatsapp_url,
    })


@login_required(login_url='/')
def my_account_address(request):
    """Gestión de direcciones del usuario"""
    return render(request, 'my-account-address.html', {
        'user': request.user
    })


@login_required(login_url='/')
def my_account_edit(request):
    """Edición de nombre, apellido, email, teléfono y cambio opcional de contraseña."""
    from django.contrib.auth import update_session_auth_hash
    from django.core.exceptions import ValidationError
    from django.contrib.auth.password_validation import validate_password

    user = request.user
    nombre_val   = user.nombre   or ''
    apellido_val = user.apellido or ''
    email_val    = user.email    or ''
    telefono_val = user.telefono or ''

    if request.method == 'POST':
        nombre_val   = request.POST.get('first_name', '').strip()
        apellido_val = request.POST.get('last_name', '').strip()
        email_val    = request.POST.get('email', '').strip().lower()
        telefono_val = request.POST.get('telefono', '').strip()

        current_password = request.POST.get('current_password', '').strip()
        new_password     = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        wants_password   = any([current_password, new_password, confirm_password])

        has_errors = False

        # Validar email
        if not email_val:
            messages.error(request, 'El email es obligatorio.')
            has_errors = True
        elif Usuario.objects.filter(email__iexact=email_val).exclude(pk=user.pk).exists():
            messages.error(request, 'Este email ya pertenece a otra cuenta.')
            has_errors = True

        # Validar cambio de contraseña (solo si se intenta)
        if wants_password:
            if not current_password:
                messages.error(request, 'Debes ingresar tu contraseña actual.')
                has_errors = True
            elif not user.check_password(current_password):
                messages.error(request, 'La contraseña actual es incorrecta.')
                has_errors = True
            if not new_password:
                messages.error(request, 'Debes ingresar la nueva contraseña.')
                has_errors = True
            elif new_password != confirm_password:
                messages.error(request, 'Las nuevas contraseñas no coinciden.')
                has_errors = True
            elif not has_errors:
                try:
                    validate_password(new_password, user=user)
                except ValidationError as exc:
                    has_errors = True
                    for msg in exc.messages:
                        messages.error(request, msg)

        if has_errors:
            return render(request, 'my-account-edit.html', {
                'user': user,
                'first_name': nombre_val,
                'last_name': apellido_val,
                'email': email_val,
                'telefono': telefono_val,
            })

        # Guardar datos de perfil
        user.nombre   = nombre_val
        user.apellido = apellido_val
        user.email    = email_val
        user.username = email_val  # por si acaso
        user.telefono = telefono_val
        user.save()

        # Cambio de contraseña
        if wants_password and not has_errors:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # mantener sesión activa
            messages.success(request, '✅ Contraseña actualizada exitosamente.')
        else:
            messages.success(request, '✅ Tus datos han sido actualizados correctamente.')

        return redirect('usuarios:my_account_edit')

    return render(request, 'my-account-edit.html', {
        'user': user,
        'first_name': nombre_val,
        'last_name': apellido_val,
        'email': email_val,
        'telefono': telefono_val,
    })


def password_reset_request(request):
    """Etapa A: Solicitar código de recuperación"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = Usuario.objects.get(email=email)
            # Invalida códigos anteriores
            PasswordResetCode.objects.filter(usuario=user, usado=False).update(usado=True)
            # Genera nuevo código
            codigo = PasswordResetCode.generar_codigo()
            PasswordResetCode.objects.create(usuario=user, codigo=codigo)
            
            # Enviar email
            exito, error_msg = enviar_email_codigo_recuperacion(request, user, codigo)
            
            if exito:
                request.session['reset_email'] = email
                return redirect('usuarios:password_reset_verify')
            else:
                messages.error(request, f'No se pudo enviar el correo: {error_msg}')
                return redirect('usuarios:password_reset_request')
            
        except Usuario.DoesNotExist:
            # Por seguridad, no decimos si el email existe o no
            # pero como estamos depurando, si no llega nada es frustrante.
            # En producción esto debería ser más sutil.
            messages.success(request, 'Si el correo está registrado, recibirás un código.')
            request.session['reset_email'] = email
            return redirect('usuarios:password_reset_verify')
            
    return render(request, 'password_reset_request.html')


def password_reset_verify(request):
    """Etapa B: Verificar el código de 6 dígitos"""
    email = request.session.get('reset_email')
    if not email:
        return redirect('usuarios:password_reset_request')

    if request.method == 'POST':
        # Combinar los 6 inputs
        codigo_enviado = "".join([
            request.POST.get('c1', ''), request.POST.get('c2', ''),
            request.POST.get('c3', ''), request.POST.get('c4', ''),
            request.POST.get('c5', ''), request.POST.get('c6', '')
        ])
        
        try:
            user = Usuario.objects.get(email=email)
            code_obj = PasswordResetCode.objects.filter(
                usuario=user, codigo=codigo_enviado, usado=False
            ).first()
            
            if code_obj and code_obj.es_valido():
                request.session['reset_code_id'] = code_obj.id
                return redirect('usuarios:password_reset_complete')
            else:
                messages.error(request, 'Código inválido o expirado.')
        except Exception:
            messages.error(request, 'Error al verificar el código.')

    return render(request, 'password_reset_verify.html', {'email': email})


def password_reset_complete(request):
    """Etapa C: Establecer nueva contraseña"""
    code_id = request.session.get('reset_code_id')
    if not code_id:
        return redirect('usuarios:password_reset_request')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('password_confirm')
        
        if password != confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'password_reset_complete.html')
            
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'password_reset_complete.html')

        try:
            code_obj = PasswordResetCode.objects.get(id=code_id, usado=False)
            user = code_obj.usuario
            user.set_password(password)
            user.save()
            
            # Marcar código como usado
            code_obj.usado = True
            code_obj.save()
            
            # Limpiar sesión
            del request.session['reset_email']
            del request.session['reset_code_id']
            
            messages.success(request, '¡Contraseña actualizada! Ya puedes iniciar sesión.')
            return redirect('usuarios:login')
        except Exception:
            messages.error(request, 'Error al actualizar la contraseña.')

    return render(request, 'password_reset_complete.html')


def password_reset_resend(request):
    """Etapa D: Reenviar código vía AJAX"""
    email = request.session.get('reset_email')
    if not email:
        return JsonResponse({'success': False, 'message': 'No hay email en sesión.'})

    try:
        user = Usuario.objects.get(email=email)
        PasswordResetCode.objects.filter(usuario=user, usado=False).update(usado=True)
        codigo = PasswordResetCode.generar_codigo()
        PasswordResetCode.objects.create(usuario=user, codigo=codigo)
        enviar_email_codigo_recuperacion(request, user, codigo)
        return JsonResponse({'success': True, 'message': 'Nuevo código enviado.'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Error al reenviar.'})



def api_ciudades_por_provincia(request, provincia_id):
    """API para obtener ciudades por provincia (AJAX)"""
    try:
        ciudades = Ciudad.objects.filter(
            provincia_id=provincia_id,
            activa=True
        ).values('id', 'nombre').order_by('nombre')
        
        return JsonResponse({
            'success': True,
            'ciudades': list(ciudades)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def verificar_email(request, token):
    """Vista para verificar el email del usuario"""
    try:
        token_obj = EmailVerificationToken.objects.get(token=token)
        
        if not token_obj.es_valido():
            messages.error(
                request, 
                '⏰ El enlace de verificación ha expirado o ya fue utilizado. '
                'Por favor solicita un nuevo correo de verificación.'
            )
            return redirect('usuarios:login')
        
        usuario = token_obj.usuario
        
        token_obj.usado = True
        token_obj.save()
        
        messages.success(
            request, 
            '✅ ¡Tu email ha sido verificado exitosamente! Ya puedes disfrutar de todas las funciones de LivenShop.'
        )
        
        return render(request, 'email_verificado.html', {
            'usuario': usuario
        })
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, '❌ El enlace de verificación no es válido o ha expirado.')
        return redirect('usuarios:login')


@login_required(login_url='/')
def reenviar_verificacion(request):
    """Vista para reenviar el correo de verificación"""
    usuario = request.user
    
    EmailVerificationToken.objects.filter(usuario=usuario, usado=False).update(usado=True)
    
    exito, msg_error = enviar_email_verificacion(request, usuario)
    if exito:
        messages.success(
            request, 
            f'Hemos enviado un nuevo correo de verificación a {usuario.email}. '
            'Por favor revisa tu bandeja de entrada (y spam).'
        )
    else:
        messages.error(
            request,
            f'Hubo un problema al enviar el correo: {msg_error}'
        )
    
    return redirect('usuarios:my_account')


@login_required(login_url='usuarios:login')
def my_account_wishlist(request):
    """Muestra los productos favoritos del usuario actual."""
    wishlist_items = Wishlist.objects.filter(
        usuario=request.user
    ).select_related('producto').prefetch_related('producto__imagenes')

    productos_favoritos = [item.producto for item in wishlist_items]

    return render(request, 'my-account-wishlist.html', {
        'user': request.user,
        'productos_favoritos': productos_favoritos,
    })


@login_required(login_url='usuarios:login')
def add_to_wishlist(request, producto_id):
    """Vista AJAX para agregar producto a la lista de deseos"""
    try:
        producto = Producto.objects.get(id=producto_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            usuario=request.user,
            producto=producto
        )
        
        if created:
            return JsonResponse({
                'success': True,
                'message': f'{producto.nombre} agregado a tu lista de deseos',
                'action': 'added'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': f'{producto.nombre} ya estaba en tu lista de deseos',
                'action': 'already_exists'
            })
    
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required(login_url='usuarios:login')
def remove_from_wishlist(request, wishlist_id):
    """Vista AJAX para eliminar producto de la lista de deseos"""
    try:
        wishlist_item = Wishlist.objects.get(id=wishlist_id, usuario=request.user)
        producto_nombre = wishlist_item.producto.nombre
        wishlist_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{producto_nombre} eliminado de tu lista de deseos'
        })
    
    except Wishlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Producto no encontrado en tu wishlist'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


def is_in_wishlist(request, producto_id):
    """Vista AJAX para verificar si un producto está en el wishlist"""
    if not request.user.is_authenticated:
        return JsonResponse({'in_wishlist': False})
    
    try:
        in_wishlist = Wishlist.objects.filter(
            usuario=request.user,
            producto_id=producto_id
        ).exists()
        
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ══════════════════════════════════════════════════════
# PANEL ADMIN — USUARIOS
# ══════════════════════════════════════════════════════

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import Q as DQ


@staff_member_required(login_url='usuarios:login')
def panel_admin_users(request):
    """
    Listado de usuarios para el panel administrativo.
    """
    search = request.GET.get('q', '').strip()
    rol_filtro = request.GET.get('rol', '').strip()
    estado_filtro = request.GET.get('estado', '').strip()

    usuarios_qs = Usuario.objects.all().order_by('-fecha_registro')

    if search:
        usuarios_qs = usuarios_qs.filter(
            DQ(email__icontains=search) |
            DQ(nombre__icontains=search) |
            DQ(apellido__icontains=search) |
            DQ(telefono__icontains=search)
        )

    if rol_filtro:
        usuarios_qs = usuarios_qs.filter(rol=rol_filtro)

    if estado_filtro == 'activo':
        usuarios_qs = usuarios_qs.filter(is_active=True)
    elif estado_filtro == 'inactivo':
        usuarios_qs = usuarios_qs.filter(is_active=False)

    paginator = Paginator(usuarios_qs, 20)
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'panel_admin/user_list.html', {
        'usuarios': usuarios,
        'total_usuarios': paginator.count,
        'search': search,
        'rol_filtro': rol_filtro,
        'estado_filtro': estado_filtro,
    })



@staff_member_required(login_url='usuarios:login')
@require_POST
def panel_admin_user_toggle_status(request, usuario_id):
    """
    Activa o desactiva un usuario vía POST/JSON.
    """
    from django.db import models as dj_models
    usuario = get_object_or_404(Usuario, pk=usuario_id)

    if usuario == request.user:
        return JsonResponse({'success': False, 'message': 'No puedes desactivar tu propia cuenta.'})

    usuario.is_active = not usuario.is_active
    usuario.save()

    accion = 'activado' if usuario.is_active else 'desactivado'
    return JsonResponse({'success': True, 'message': f'Usuario {accion} correctamente.', 'is_active': usuario.is_active})

# ==============================================================================
# NOTIFICACIONES ADMIN (CAMPANITA)
# ==============================================================================
@login_required
def api_notificaciones_admin(request):
    """Devuelve las últimas notificaciones no leídas para la campanita del admin"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    notificaciones = NotificacionAdmin.objects.filter(leido=False).order_by('-fecha_creacion')[:10]
    total_no_leidas = NotificacionAdmin.objects.filter(leido=False).count()
    
    html = ""
    if not notificaciones:
        html = '<div style="padding: 20px; text-align: center; color: #888; font-size: 13px;">No hay notificaciones nuevas.</div>'
    else:
        for notif in notificaciones:
            from django.urls import reverse
            url_ir = reverse('usuarios:ir_notificacion_admin', args=[notif.id])
            
            # Seleccionar icono según tipo
            if notif.tipo == 'pedido':
                icono = '<i class="icon-shopping-cart" style="font-size: 16px;"></i>'
                icono_bg = '#fef3c7'
                icono_color = '#d97706'
            else:
                icono = '<i class="icon-heart" style="font-size: 16px;"></i>'
                icono_bg = '#fce7f3'
                icono_color = '#db2777'
                
            fecha_str = notif.fecha_creacion.strftime("%d %b %H:%M")
            
            html += f'''
            <a href="{url_ir}" style="display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; border-bottom: 1px solid #f0ece6; text-decoration: none; transition: background 0.2s; background: #fff;" onmouseover="this.style.background='#fafaf9'" onmouseout="this.style.background='#fff'">
                <div style="background: {icono_bg}; color: {icono_color}; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    {icono}
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 13px; color: #1a1a1a; font-weight: 600; line-height: 1.3; margin-bottom: 4px;">{notif.mensaje}</div>
                    <div style="font-size: 11px; color: #888;">{fecha_str}</div>
                </div>
            </a>
            '''
            
    return JsonResponse({
        'count': total_no_leidas,
        'html': html
    })

@login_required
def ir_notificacion_admin(request, notificacion_id):
    """Marca la notificación como leída y redirige al destino"""
    if not request.user.is_staff:
        return redirect('home')
        
    notif = get_object_or_404(NotificacionAdmin, id=notificacion_id)
    notif.leido = True
    notif.save()
    
    return redirect(notif.url)
