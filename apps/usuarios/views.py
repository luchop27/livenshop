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
from .models import Usuario, EmailVerificationToken, Provincia, Ciudad, Wishlist
from apps.productos.models import Producto
import base64
import os


def limpiar_mensajes_pendientes(request):
    """Consume mensajes pendientes para evitar arrastre entre panel admin y frontend."""
    storage = get_messages(request)
    storage.used = True


def obtener_logo_base64():
    """Convierte el logo a base64 para usar en emails"""
    try:
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'images', 'logo', 'logoselena.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo', 'logoselena.png')
        
        with open(logo_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Error cargando logo: {e}")
        return ""


def enviar_email_directo(destinatario, asunto, mensaje_html, incluir_logo=True):
    """
    Función para enviar emails usando smtplib directamente con SSL
    Evita problemas de certificados en Windows
    Adjunta el logo como imagen embebida usando Content-ID
    """
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    
    try:
        print(f"🔧 Iniciando envío de email a {destinatario}")
        print(f"📧 Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"👤 Usuario: {settings.EMAIL_HOST_USER}")
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        print("✅ Contexto SSL creado (sin verificación de certificados)")
        
        msg = MIMEMultipart('related')
        msg['Subject'] = asunto
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = destinatario
        
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)
        
        html_part = MIMEText(mensaje_html, 'html', 'utf-8')
        msg_alternative.attach(html_part)
        
        if incluir_logo:
            try:
                logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'images', 'logo', 'logoselena.png')
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo', 'logoselena.png')
                
                with open(logo_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img = MIMEImage(img_data, 'png')
                    img.add_header('Content-ID', '<logoselena>')
                    img.add_header('Content-Disposition', 'inline', filename='logoselena.png')
                    msg.attach(img)
                    print("✅ Logo adjuntado como imagen embebida")
            except Exception as e:
                print(f"⚠️ No se pudo adjuntar el logo: {e}")
        
        print("✅ Mensaje creado")
        
        print(f"🔌 Conectando a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context) as server:
            print("✅ Conexión establecida")
            
            print("🔐 Autenticando...")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            print("✅ Autenticación exitosa")
            
            print("📤 Enviando mensaje...")
            server.sendmail(settings.EMAIL_HOST_USER, destinatario, msg.as_string())
            print("✅ Mensaje enviado")
        
        print(f"✅✅✅ Email enviado exitosamente a {destinatario}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación: {e}")
        print("⚠️ Verifica que:")
        print("   1. La verificación en 2 pasos esté activada en Gmail")
        print("   2. Hayas generado una 'Contraseña de aplicación' en https://myaccount.google.com/apppasswords")
        print("   3. La contraseña sea exactamente 16 caracteres SIN ESPACIOS")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {e}")
        return False
    except ssl.SSLError as e:
        print(f"❌ Error SSL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general enviando email: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


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
        resultado = enviar_email_directo(usuario.email, asunto, mensaje_html)
        return resultado
        
    except Exception as e:
        print(f"Error en enviar_email_verificacion: {e}")
        import traceback
        traceback.print_exc()
        return False


def login_usuario(request):
    """Vista de login para usuarios"""
    limpiar_mensajes_pendientes(request)

    if request.user.is_authenticated:
        if request.user.rol == 'admin_tienda' or request.user.is_staff:
            return redirect('core:admin_index')
        return redirect('usuarios:my_account')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            
            if user.rol == 'admin_tienda' or user.is_staff:
                return redirect('core:admin_index')
            
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            
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
        provincia_id = request.POST.get('provincia')
        ciudad_id = request.POST.get('ciudad')
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        if not provincia_id or not ciudad_id:
            messages.error(request, 'Debes seleccionar una provincia y una ciudad/cantón.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
        
        if not email or not password:
            messages.error(request, 'El email y la contraseña son obligatorios.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
        
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
        
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este email ya está registrado.')
            return render(request, 'register.html', construir_contexto_registro(
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                provincia_id=provincia_id,
                ciudad_id=ciudad_id,
            ))
        
        try:
            provincia = None
            ciudad = None
            
            if provincia_id:
                try:
                    provincia = Provincia.objects.get(id=provincia_id, activa=True)
                except Provincia.DoesNotExist:
                    provincia = None

            if not provincia:
                messages.error(request, 'La provincia seleccionada no es válida.')
                return render(request, 'register.html', construir_contexto_registro(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono,
                    provincia_id=provincia_id,
                    ciudad_id=ciudad_id,
                ))
            
            if ciudad_id:
                try:
                    ciudad = Ciudad.objects.get(id=ciudad_id, provincia=provincia, activa=True)
                except Ciudad.DoesNotExist:
                    ciudad = None

            if not ciudad:
                messages.error(request, 'La ciudad/cantón seleccionada no pertenece a la provincia elegida.')
                return render(request, 'register.html', construir_contexto_registro(
                    nombre=nombre,
                    apellido=apellido,
                    email=email,
                    telefono=telefono,
                    provincia_id=provincia_id,
                    ciudad_id=ciudad_id,
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
    ordenes = request.user.pedidos.all().order_by('-created_at')
    
    from django.core.paginator import Paginator
    paginator = Paginator(ordenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'my-account-orders.html', {
        'user': request.user,
        'ordenes': page_obj,
    })


@login_required(login_url='/')
def my_account_orders_details(request, numero_pedido):
    """Detalles de una orden específica"""
    from apps.core.models import Pedido
    
    orden = get_object_or_404(Pedido, numero_pedido=numero_pedido, usuario=request.user)
    
    return render(request, 'my-account-orders-details.html', {
        'user': request.user,
        'orden': orden,
    })


@login_required(login_url='/')
def my_account_address(request):
    """Gestión de direcciones del usuario"""
    return render(request, 'my-account-address.html', {
        'user': request.user
    })


@login_required(login_url='/')
def my_account_edit(request):
    """Edición de detalles de la cuenta"""
    if request.method == 'POST':
        messages.success(request, 'Información actualizada correctamente.')
        return redirect('usuarios:my_account_edit')
    
    return render(request, 'my-account-edit.html', {
        'user': request.user
    })


def password_reset_request(request):
    """Vista para solicitar restablecimiento de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Por favor ingresa tu email.')
            return redirect('usuarios:login')
        
        try:
            user = Usuario.objects.get(email=email)
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            from django.urls import reverse
            reset_path = reverse('usuarios:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            reset_url = request.build_absolute_uri(reset_path)
            
            logo_src = "cid:logoselena"
            nombre_usuario = user.nombre or user.email.split('@')[0]
            
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
                        font-size: 28px;
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
                        font-size: 20px;
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
                    .divider {{
                        height: 1px;
                        background: linear-gradient(to right, transparent, #d4cfc4, transparent);
                        margin: 30px 0;
                    }}
                    .security-info {{
                        background: linear-gradient(to bottom, #faf9f7, #ffffff);
                        border: 2px solid #e8e3da;
                        border-left: 4px solid #918567;
                        padding: 20px;
                        margin: 30px 0;
                        border-radius: 8px;
                    }}
                    .security-info h3 {{
                        color: #918567;
                        margin: 0 0 10px;
                        font-size: 16px;
                    }}
                    .security-info p {{
                        margin: 5px 0;
                        color: #666;
                        font-size: 14px;
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
                        <h1 class="header-title">🔐 Restablecer Contraseña</h1>
                        <p class="header-subtitle">Solicitud de cambio de contraseña</p>
                    </div>
                    
                    <div class="content">
                        <p class="greeting">Hola <strong>{nombre_usuario}</strong>,</p>
                        
                        <p class="message">
                            Recibimos una solicitud para restablecer la contraseña de tu cuenta en <strong>LivenShop</strong>. 
                            Si realizaste esta solicitud, haz clic en el botón de abajo para crear una nueva contraseña.
                        </p>
                        
                        <div class="btn-container">
                            <a href="{reset_url}" class="btn">
                                🔑 Restablecer mi Contraseña
                            </a>
                        </div>
                        
                        <div class="security-info">
                            <h3>🛡️ Información de Seguridad</h3>
                            <p>• Este enlace expira en <strong>24 horas</strong></p>
                            <p>• Solo funciona una vez</p>
                            <p>• Si no solicitaste este cambio, ignora este correo y tu contraseña permanecerá segura</p>
                        </div>
                        
                        <div class="divider"></div>
                        
                        <div class="link-alternative">
                            <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                            <a href="{reset_url}">{reset_url}</a>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p class="footer-text">Este correo fue enviado automáticamente. Por favor no respondas.</p>
                        <p class="footer-text">© 2026 LivenShop - Todos los derechos reservados</p>
                        <p class="footer-text" style="margin-top: 15px;">
                            ¿No solicitaste este cambio? <a href="mailto:soporte@livenshop.com">Contáctanos</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            asunto = '🔐 Restablece tu contraseña - LivenShop'
            
            if enviar_email_directo(user.email, asunto, mensaje_html):
                messages.success(
                    request, 
                    '✅ Se ha enviado un correo con las instrucciones para restablecer tu contraseña. '
                    'Revisa tu bandeja de entrada.'
                )
            else:
                messages.error(
                    request, 
                    '❌ Hubo un problema al enviar el correo. Por favor intenta nuevamente.'
                )
                
        except Usuario.DoesNotExist:
            messages.success(
                request, 
                '✅ Si el email existe en nuestro sistema, recibirás un correo con las instrucciones.'
            )
        
        return redirect('usuarios:login')
    
    return redirect('usuarios:login')


def password_reset_confirm(request, uidb64, token):
    """Vista para confirmar y establecer nueva contraseña"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password', '').strip()
            password_confirm = request.POST.get('password_confirm', '').strip()
            
            if not password:
                messages.error(request, 'La contraseña es obligatoria.')
                return render(request, 'password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            if password != password_confirm:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            if len(password) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return render(request, 'password_reset_confirm.html', {
                    'validlink': True,
                    'uidb64': uidb64,
                    'token': token
                })
            
            user.set_password(password)
            user.save()
            
            messages.success(request, '¡Tu contraseña ha sido restablecida exitosamente! Ya puedes iniciar sesión.')
            return redirect('usuarios:login')
        
        return render(request, 'password_reset_confirm.html', {
            'validlink': True,
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 'El enlace de restablecimiento es inválido o ha expirado.')
        return redirect('usuarios:login')


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
    
    if enviar_email_verificacion(request, usuario):
        messages.success(
            request, 
            f'Hemos enviado un nuevo correo de verificación a {usuario.email}. '
            'Por favor revisa tu bandeja de entrada (y spam).'
        )
    else:
        messages.error(
            request,
            'Hubo un problema al enviar el correo. Por favor intenta más tarde.'
        )
    
    return redirect('usuarios:my_account')


@login_required(login_url='usuarios:login')
def my_account_wishlist(request):
    """Redirige al listado principal de favoritos."""
    return redirect('core:wishlist')


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
