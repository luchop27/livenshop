from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    verbose_name = 'Usuarios'
    
    def ready(self):
        """Se ejecuta cuando Django carga la app"""
        import apps.usuarios.signals
