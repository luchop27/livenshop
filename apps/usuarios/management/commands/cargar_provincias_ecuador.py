"""
Comando para cargar las provincias y ciudades del Ecuador en la base de datos.

Uso: python manage.py cargar_provincias_ecuador
"""

from django.core.management.base import BaseCommand
from apps.usuarios.models import Provincia, Ciudad


class Command(BaseCommand):
    help = 'Carga las provincias y ciudades del Ecuador en la base de datos'

    def handle(self, *args, **options):
        # Datos de provincias y ciudades del Ecuador
        datos = {
            'Azuay': ['Cuenca', 'Gualaceo', 'Sigsig', 'Girón', 'Nabón'],
            'Bolívar': ['Guaranda', 'Caluma', 'Chillanes', 'San Miguel'],
            'Cañar': ['Azogues', 'Cañar', 'Déleg', 'Suscal'],
            'Carchi': ['Tulcán', 'Ibarra', 'Otavalo', 'Cotacachi'],
            'Chimborazo': ['Riobamba', 'Guaranda', 'Latacunga'],
            'Cotopaxi': ['Latacunga', 'La Maná', 'Salcedo', 'Saquisilí'],
            'El Oro': ['Machala', 'Santa Rosa', 'Pasaje', 'Balsas'],
            'Esmeraldas': ['Esmeraldas', 'Atacames', 'Muisne', 'Rioverde'],
            'Galápagos': ['Puerto Baquerizo', 'Puerto Ayora', 'Puerto Villamil'],
            'Guayas': ['Guayaquil', 'Daule', 'Durán', 'Samborondón', 'Yaguachi'],
            'Imbabura': ['Ibarra', 'Otavalo', 'Cotacachi', 'Pimampiro'],
            'Loja': ['Loja', 'Catamayo', 'Saraguro', 'Macará'],
            'Los Ríos': ['Babahoyo', 'Vinces', 'Baba', 'Pueblo Viejo'],
            'Manabí': ['Portoviejo', 'Manta', 'Montecristi', 'Jipijapa'],
            'Morona Santiago': ['Macas', 'Gualaquiza', 'Limón', 'Sucúa'],
            'Napo': ['Tena', 'Archidona', 'Puyo'],
            'Orellana': ['Francisco de Orellana', 'Coca', 'Loreto'],
            'Pastaza': ['Puyo', 'Tena', 'Mera'],
            'Pichincha': ['Quito', 'Latacunga', 'Machachi', 'Ibarra'],
            'Santa Elena': ['Santa Elena', 'Salinas', 'La Libertad'],
            'Santo Domingo': ['Santo Domingo', 'La Concordia'],
            'Sucumbíos': ['Nueva Loja', 'Lago Agrio', 'Cuyabeno'],
            'Tungurahua': ['Ambato', 'Latacunga', 'Riobamba'],
            'Zamora Chinchipe': ['Zamora', 'Yantzaza', 'Zumbi'],
        }

        provincias_creadas = 0
        ciudades_creadas = 0

        for provincia_nombre, ciudades_lista in datos.items():
            # Crear o obtener provincia
            provincia, creada = Provincia.objects.get_or_create(
                nombre=provincia_nombre,
                defaults={'activa': True}
            )
            
            if creada:
                provincias_creadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Provincia "{provincia_nombre}" creada')
                )
            
            # Crear ciudades
            for ciudad_nombre in ciudades_lista:
                ciudad, creada = Ciudad.objects.get_or_create(
                    nombre=ciudad_nombre,
                    provincia=provincia,
                    defaults={'activa': True}
                )
                
                if creada:
                    ciudades_creadas += 1
                    self.stdout.write(f'  ✓ Ciudad "{ciudad_nombre}" creada')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Carga completada: '
                f'{provincias_creadas} provincias, '
                f'{ciudades_creadas} ciudades'
            )
        )
