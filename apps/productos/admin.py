from django.contrib import admin
from .models import (
    Coleccion, Categoria, Producto, Imagen, Atributo, 
    AtributoProducto, CarritoItem, ShippingInfo, ReturnPolicy
)


# =====================
# INLINES
# =====================
class ImagenInline(admin.TabularInline):
    model = Imagen
    extra = 1
    fields = ['tipo_medio', 'imagen', 'video', 'url', 'posicion', 'es_principal']


class AtributoProductoInline(admin.TabularInline):
    model = AtributoProducto
    extra = 1
    fields = ['atributo', 'valor']


# =====================
# PRODUCT ADMIN
# =====================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'precio_oferta', 'stock', 'activo', 'destacado']
    list_filter = ['activo', 'destacado', 'categoria', 'coleccion', 'created_at']
    search_fields = ['nombre', 'descripcion_corta', 'descripcion_larga', 'marca']
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ImagenInline, AtributoProductoInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'categoria', 'coleccion')
        }),
        ('Descripción', {
            'fields': ('descripcion_corta', 'descripcion_larga'),
            'classes': ('collapse',)
        }),
        ('Precios y Stock', {
            'fields': ('precio', 'precio_oferta', 'stock')
        }),
        ('Detalles del Producto', {
            'fields': ('marca', 'dimensiones', 'material'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('activo', 'destacado')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Fechas de creación y última actualización'
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


# =====================
# CATEGORY ADMIN
# =====================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'padre', 'coleccion', 'posicion', 'activo']
    list_filter = ['activo', 'coleccion', 'padre']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion')
        }),
        ('Jerarquía', {
            'fields': ('padre', 'coleccion')
        }),
        ('Imagen y Orden', {
            'fields': ('imagen', 'posicion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


# =====================
# COLLECTION ADMIN
# =====================
@admin.register(Coleccion)
class ColeccionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'destacada', 'created_at']
    list_filter = ['activo', 'destacada', 'created_at']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'slug', 'descripcion')
        }),
        ('Imagen', {
            'fields': ('imagen',)
        }),
        ('Estado', {
            'fields': ('activo', 'destacada')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


# =====================
# ATTRIBUTE ADMIN
# =====================
@admin.register(Atributo)
class AtributoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'posicion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    prepopulated_fields = {'slug': ('nombre',)}
    fieldsets = (
        ('Información', {
            'fields': ('nombre', 'slug', 'posicion', 'activo')
        }),
    )


# =====================
# IMAGE ADMIN
# =====================
@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo_medio', 'es_principal', 'posicion']
    list_filter = ['tipo_medio', 'es_principal', 'created_at']
    search_fields = ['producto__nombre']
    fieldsets = (
        ('Información', {
            'fields': ('producto', 'tipo_medio')
        }),
        ('Contenido', {
            'fields': ('imagen', 'video', 'url'),
            'description': 'Sube un archivo o proporciona una URL'
        }),
        ('Presentación', {
            'fields': ('posicion', 'es_principal')
        }),
    )
    readonly_fields = ['created_at']


# =====================
# ATTRIBUTE PRODUCT ADMIN
# =====================
@admin.register(AtributoProducto)
class AtributoProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'atributo', 'valor']
    list_filter = ['atributo', 'producto__categoria']
    search_fields = ['producto__nombre', 'valor']


# =====================
# CARRITO ADMIN
# =====================
@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'producto', 'cantidad', 'precio', 'total_precio', 'fecha_agregado']
    list_filter = ['usuario', 'fecha_agregado']
    search_fields = ['usuario__email', 'producto__nombre']
    readonly_fields = ['total_precio', 'fecha_agregado', 'fecha_actualizado']
    fieldsets = (
        ('Información del Carrito', {
            'fields': ('usuario', 'producto', 'cantidad', 'precio')
        }),
        ('Totales', {
            'fields': ('total_precio',)
        }),
        ('Metadata', {
            'fields': ('fecha_agregado', 'fecha_actualizado'),
            'classes': ('collapse',)
        }),
    )


# =====================
# SHIPPING INFO ADMIN
# =====================
@admin.register(ShippingInfo)
class ShippingInfoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'activo']
    fieldsets = (
        ('Información de Envío', {
            'fields': ('titulo', 'descripcion')
        }),
        ('Tiempos de Entrega', {
            'fields': ('tiempo_nacional', 'tiempo_internacional')
        }),
        ('Costos', {
            'fields': ('costo_envio', 'envio_gratis_desde')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


# =====================
# RETURN POLICY ADMIN
# =====================
@admin.register(ReturnPolicy)
class ReturnPolicyAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'dias_devolucion', 'orden', 'activo']
    list_filter = ['activo']
    fieldsets = (
        ('Información de Política', {
            'fields': ('titulo', 'descripcion', 'icono')
        }),
        ('Detalles', {
            'fields': ('dias_devolucion', 'orden', 'activo')
        }),
    )
