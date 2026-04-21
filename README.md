# LivenShop - E-Commerce de Decoración del Hogar

Plataforma e-commerce basada en Django para venta de artículos de decoración del hogar en Ecuador.

## 🚀 Instalación y Setup

### 1. Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Migraciones de Base de Datos

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### 4. Cargar Provincias y Ciudades del Ecuador

```bash
python manage.py cargar_provincias_ecuador
```

### 5. Crear Superuser (Administrador)

```bash
python manage.py createsuperuser
```

Ingresar email y contraseña. El email se usará como username.

### 6. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Acceder a: `http://localhost:8000`

Admin: `http://localhost:8000/admin`

---

## 📁 Estructura del Proyecto

```
livenshop/
├── apps/
│   ├── productos/          # App de productos, catálogo y carrito
│   │   ├── models.py       # Modelos: Producto, Categoria, Imagen, etc.
│   │   ├── views.py        # Class-based views
│   │   ├── urls.py         # Rutas de productos
│   │   ├── admin.py        # Admin de productos
│   │   └── context_processors.py
│   │
│   └── usuarios/           # App de usuarios y autenticación
│       ├── models.py       # Modelos: Usuario, Provincia, Ciudad, Wishlist
│       ├── views.py        # Vistas de login, registro, perfil
│       ├── urls.py         # Rutas de usuarios
│       ├── admin.py        # Admin de usuarios
│       ├── signals.py      # Señales automáticas
│       ├── emails.py       # Utilidades de email
│       └── management/     # Comandos personalizados
│           └── commands/
│               └── cargar_provincias_ecuador.py
│
├── liven/                  # Configuración del proyecto
│   ├── settings.py         # Configuraciones de Django
│   ├── urls.py             # URLs principales
│   └── wsgi.py
│
├── templates/              # Templates HTML globales
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
├── media/                  # Archivos subidos por usuarios
├── manage.py               # Script de administración
├── db.sqlite3              # Base de datos SQLite (desarrollo)
└── requirements.txt        # Dependencias Python
```

---

## 🔑 Funcionalidades Principales

### App Productos
- **Catálogo dinámico** con categorías y colecciones
- **Búsqueda y filtrado** de productos
- **Carrito de compras** persistente por usuario
- **Atributos personalizables** (material, dimensiones, etc.)
- **Galería de imágenes** y videos
- **Productos relacionados** en detalle

### App Usuarios
- **Registro y autenticación** con email
- **Recuperación de contraseña** con código de 6 dígitos
- **Verificación de email** con token UUID
- **Panel de usuario** con mi cuenta, pedidos, favoritos
- **Sistema de favoritos (Wishlist)** 
- **Geolocalización** con provincias y ciudades del Ecuador
- **Roles de usuario**: Cliente y Administrador de Tienda
- **Tracking de cupones** especiales (ej: carnaval 2026)

---

## ⚙️ Configuración Importante

### Email (En Desarrollo)
Por defecto, los emails se muestran en la consola. Para producción, configurar en `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_app_password'  # App password, no contraseña
DEFAULT_FROM_EMAIL = 'no-reply@livenshop.com'
```

### Base de Datos
- Desarrollo: SQLite (db.sqlite3)
- Producción: Cambiar `DATABASES` en `settings.py` a PostgreSQL o MySQL

### Media Files
- Los archivos subidos se guardan en `/media/`
- En desarrollo, se sirven automáticamente
- En producción, usar servidor web (nginx, Apache) o CDN

---

## 🛠️ Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Ver migraciones pendientes
python manage.py showmigrations

# Aplicar migraciones
python manage.py migrate

# Cargar provincias del Ecuador
python manage.py cargar_provincias_ecuador

# Crear superuser
python manage.py createsuperuser

# Shell interactivo de Django
python manage.py shell

# Recolectar archivos estáticos (producción)
python manage.py collectstatic

# Hacer backup de BD
python manage.py dumpdata > backup.json

# Restaurar backup de BD
python manage.py loaddata backup.json

# Servidor de desarrollo
python manage.py runserver

# Servidor en puerto diferente
python manage.py runserver 0.0.0.0:8001
```

---

## 🔐 Seguridad (Importante para Producción)

```python
# settings.py (CAMBIAR ESTOS VALORES EN PRODUCCIÓN)
DEBUG = False  # Nunca True en producción
SECRET_KEY = 'cambiar-a-clave-secreta-aleatoria'
ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com']
CSRF_TRUSTED_ORIGINS = ['https://tu-dominio.com']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

---

## 📧 Envío de Emails

Los emails se disparan automáticamente en:
1. **Registro de usuario**: Email de verificación
2. **Recuperación de contraseña**: Código de 6 dígitos
3. **Cambio de contraseña**: Confirmación

En desarrollo, los emails se muestran en la consola. Descomentar envíos en:
- `apps/usuarios/signals.py`
- `apps/usuarios/views.py` (en las funciones correspondientes)

---

## 🔗 URLs Principales

### Públicas
- `/` - Home
- `/productos/` - Catálogo de productos
- `/producto/<slug>/` - Detalle de producto
- `/categoria/<slug>/` - Productos por categoría
- `/coleccion/<slug>/` - Productos por colección

### Autenticación
- `/usuarios/login/` - Login
- `/usuarios/register/` - Registro
- `/usuarios/logout/` - Logout

### Panel de Usuario (Requiere login)
- `/usuarios/mi-cuenta/` - Panel principal
- `/usuarios/mi-cuenta/pedidos/` - Mis pedidos
- `/usuarios/mi-cuenta/direcciones/` - Mis direcciones
- `/usuarios/mi-cuenta/detalles/` - Editar perfil
- `/usuarios/mi-cuenta/favoritos/` - Mis favoritos

### Admin
- `/admin/` - Dashboard administrativo

---

## 📱 Responsividad

El proyecto incluye Bootstrap para responsividad. Los templates personalizados deben usar:

```html
<!-- Bootstrap CSS (ya en static) -->
<link rel="stylesheet" href="{% static 'css/bootstrap.min.css' %}">

<!-- Bootstrap JS -->
<script src="{% static 'js/bootstrap.min.js' %}"></script>

<!-- jQuery para AJAX -->
<script src="{% static 'js/jquery.min.js' %}"></script>
```

---

## 🐛 Troubleshooting

### Error: "django_tables2 no existe"
```bash
pip install django-tables2
```

### Error: "Pillow no tiene formato JPG"
```bash
pip install --upgrade Pillow
```

### Error: "ALLOWED_HOSTS no válido"
Cambiar en `settings.py`:
```python
ALLOWED_HOSTS = ['*']  # Solo para desarrollo
```

### Base de datos bloqueada (SQLite)
```bash
# Resetear base de datos (CUIDADO - elimina todo)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## 📝 Licencia

Privada - Proyecto de LivenShop

---

## 👤 Autor

Desarrollado para LivenShop

---

## 📞 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.
