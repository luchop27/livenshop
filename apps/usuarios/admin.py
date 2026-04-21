from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario, Ciudad, Provincia, Wishlist, EmailVerificationToken, PasswordResetCode


def delete_provincias(modeladmin, request, queryset):
    """Acción personalizada para eliminar provincias seleccionadas"""
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f'{count} provincia(s) eliminada(s) correctamente.')

delete_provincias.short_description = "🗑️ Eliminar provincias seleccionadas"


def delete_ciudades(modeladmin, request, queryset):
    """Acción personalizada para eliminar ciudades seleccionadas"""
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f'{count} ciudad(es) eliminada(s) correctamente.')

delete_ciudades.short_description = "🗑️ Eliminar ciudades seleccionadas"


def activate_usuarios(modeladmin, request, queryset):
    """Acción personalizada para activar usuarios seleccionados"""
    count = queryset.update(is_active=True)
    modeladmin.message_user(request, f'{count} usuario(s) activado(s) correctamente.')

activate_usuarios.short_description = "✓ Activar usuarios seleccionados"


def deactivate_usuarios(modeladmin, request, queryset):
    """Acción personalizada para desactivar usuarios seleccionados"""
    count = queryset.update(is_active=False)
    modeladmin.message_user(request, f'{count} usuario(s) desactivado(s) correctamente.')

deactivate_usuarios.short_description = "✗ Desactivar usuarios seleccionados"


def delete_usuarios(modeladmin, request, queryset):
    """Acción personalizada para eliminar usuarios seleccionados"""
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f'{count} usuario(s) eliminado(s) correctamente.')

delete_usuarios.short_description = "🗑️ Eliminar usuarios seleccionados"


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    ordering = ('nombre',)
    actions = [delete_provincias]


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'codigo_postal', 'activa')
    list_filter = ('activa', 'provincia')
    search_fields = ('nombre', 'provincia__nombre')
    ordering = ('provincia', 'nombre')
    actions = [delete_ciudades]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('email', 'nombre_completo', 'telefono', 'ciudad', 'rol_badge', 'estado_badge', 'fecha_registro')
    list_filter = ('rol', 'is_active', 'provincia', 'ciudad', 'fecha_registro')
    ordering = ('-fecha_registro',)
    search_fields = ('email', 'nombre', 'apellido', 'telefono')
    actions = [activate_usuarios, deactivate_usuarios, delete_usuarios]
    date_hierarchy = 'fecha_registro'

    fieldsets = (
        (None, {
            'fields': ('email', 'password'),
            'description': 'Credenciales de acceso del usuario'
        }),
        ('Información personal', {
            'fields': ('nombre', 'apellido', 'telefono', 'provincia', 'ciudad'),
            'description': 'Datos personales del usuario'
        }),
        ('Permisos y Estado', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Control de permisos y estado de la cuenta'
        }),
        ('Información del Sistema', {
            'fields': ('fecha_registro', 'fecha_edicion', 'last_login'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
            'description': 'Ingresa el email y contraseña del nuevo usuario'
        }),
        ('Información personal', {
            'fields': ('nombre', 'apellido', 'telefono', 'provincia', 'ciudad'),
        }),
        ('Configuración', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('fecha_registro', 'fecha_edicion', 'last_login')

    def nombre_completo(self, obj):
        """Muestra el nombre completo del usuario"""
        return obj.get_full_name()
    nombre_completo.short_description = 'Nombre Completo'

    def rol_badge(self, obj):
        """Muestra el rol del usuario con colores"""
        if obj.rol == 'admin_tienda':
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                obj.get_rol_display()
            )
        else:
            return format_html(
                '<span style="background-color: #95a5a6; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                obj.get_rol_display()
            )
    rol_badge.short_description = 'Rol'

    def estado_badge(self, obj):
        """Muestra el estado del usuario con colores"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Activo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Inactivo</span>'
            )
    estado_badge.short_description = 'Estado'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto', 'agregado')
    list_filter = ('agregado', 'usuario')
    search_fields = ('usuario__email', 'producto__nombre')
    ordering = ('-agregado',)
    date_hierarchy = 'agregado'
    readonly_fields = ('agregado',)


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'token_corto', 'creado', 'usado', 'es_valido')
    list_filter = ('usado', 'creado')
    search_fields = ('usuario__email', 'token')
    ordering = ('-creado',)
    readonly_fields = ('token', 'creado')
    
    def token_corto(self, obj):
        """Muestra una versión corta del token"""
        return f"{obj.token[:8]}..." if obj.token else ""
    token_corto.short_description = 'Token'
    
    def es_valido(self, obj):
        """Muestra si el token es válido"""
        valido = obj.es_valido()
        if valido:
            return format_html('<span style="color: #27ae60; font-weight: bold;">✓ Válido</span>')
        else:
            return format_html('<span style="color: #e74c3c; font-weight: bold;">✗ Expirado</span>')
    es_valido.short_description = 'Estado'


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'codigo', 'creado', 'usado', 'tiempo_restante_display')
    list_filter = ('usado', 'creado')
    search_fields = ('usuario__email', 'codigo')
    ordering = ('-creado',)
    readonly_fields = ('codigo', 'creado', 'expira_en')
    
    def tiempo_restante_display(self, obj):
        """Muestra el tiempo restante formateado"""
        tiempo = obj.tiempo_restante()
        if tiempo <= 0:
            return format_html('<span style="color: #e74c3c; font-weight: bold;">Expirado</span>')
        minutos = tiempo // 60
        segundos = tiempo % 60
        return f"{minutos}m {segundos}s"
    tiempo_restante_display.short_description = 'Tiempo Restante'
