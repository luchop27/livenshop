import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'liven.settings')
django.setup()

from apps.usuarios.models import Provincia, Ciudad

# Lista completa de ciudades del Ecuador
ciudades_ecuador = [
    # Azuay
    ('Cuenca', 'Azuay', '010101'),
    ('Gualaceo', 'Azuay', '010102'),
    ('Paute', 'Azuay', '010103'),
    ('Sígsig', 'Azuay', '010104'),
    ('Chordeleg', 'Azuay', '010105'),
    
    # Bolívar
    ('Guaranda', 'Bolívar', '020101'),
    ('Caluma', 'Bolívar', '020102'),
    ('Chillanes', 'Bolívar', '020103'),
    ('Echeandía', 'Bolívar', '020104'),
    ('San Miguel', 'Bolívar', '020105'),
    
    # Cañar
    ('Azogues', 'Cañar', '030101'),
    ('La Troncal', 'Cañar', '030102'),
    ('Cañar', 'Cañar', '030103'),
    ('El Tambo', 'Cañar', '030104'),
    
    # Carchi
    ('Tulcán', 'Carchi', '040101'),
    ('San Gabriel', 'Carchi', '040102'),
    ('Espejo', 'Carchi', '040103'),
    ('Montúfar', 'Carchi', '040104'),
    
    # Chimborazo
    ('Riobamba', 'Chimborazo', '050101'),
    ('Latacunga', 'Chimborazo', '050102'),
    ('Ambato', 'Chimborazo', '050103'),
    ('Guaranda', 'Chimborazo', '050104'),
    ('Penipe', 'Chimborazo', '050105'),
    
    # Cotopaxi
    ('Latacunga', 'Cotopaxi', '060101'),
    ('La Maná', 'Cotopaxi', '060102'),
    ('Pangua', 'Cotopaxi', '060103'),
    ('Salcedo', 'Cotopaxi', '060104'),
    
    # El Oro
    ('Machala', 'El Oro', '070101'),
    ('Santa Rosa', 'El Oro', '070102'),
    ('Huaquillas', 'El Oro', '070103'),
    ('Pasaje', 'El Oro', '070104'),
    ('Piñas', 'El Oro', '070105'),
    
    # Esmeraldas
    ('Esmeraldas', 'Esmeraldas', '080101'),
    ('Atacames', 'Esmeraldas', '080102'),
    ('Muisne', 'Esmeraldas', '080103'),
    ('Quinindé', 'Esmeraldas', '080104'),
    ('San Lorenzo', 'Esmeraldas', '080105'),
    
    # Guayas
    ('Guayaquil', 'Guayas', '090101'),
    ('Durán', 'Guayas', '090102'),
    ('Samborondón', 'Guayas', '090103'),
    ('Daule', 'Guayas', '090104'),
    ('Milagro', 'Guayas', '090105'),
    ('Balzar', 'Guayas', '090106'),
    ('Yaguachi', 'Guayas', '090107'),
    
    # Imbabura
    ('Ibarra', 'Imbabura', '100101'),
    ('Otavalo', 'Imbabura', '100102'),
    ('Antonio Ante', 'Imbabura', '100103'),
    ('Cotacachi', 'Imbabura', '100105'),
    
    # Loja
    ('Loja', 'Loja', '110101'),
    ('Catamayo', 'Loja', '110102'),
    ('Macará', 'Loja', '110103'),
    ('Vilcabamba', 'Loja', '110104'),
    ('Saraguro', 'Loja', '110105'),
    
    # Los Ríos
    ('Babahoyo', 'Los Ríos', '120101'),
    ('Quevedo', 'Los Ríos', '120102'),
    ('Vinces', 'Los Ríos', '120103'),
    ('Baba', 'Los Ríos', '120104'),
    ('Mocache', 'Los Ríos', '120105'),
    
    # Manabí
    ('Manta', 'Manabí', '130101'),
    ('Portoviejo', 'Manabí', '130102'),
    ('Bahía de Caráquez', 'Manabí', '130103'),
    ('Jipijapa', 'Manabí', '130104'),
    ('El Carmen', 'Manabí', '130105'),
    ('Chone', 'Manabí', '130106'),
    
    # Morona Santiago
    ('Macas', 'Morona Santiago', '140101'),
    ('Sucúa', 'Morona Santiago', '140102'),
    ('Palora', 'Morona Santiago', '140103'),
    ('Tena', 'Morona Santiago', '140104'),
    ('Puyo', 'Morona Santiago', '140105'),
    
    # Napo
    ('Tena', 'Napo', '150101'),
    ('Archidona', 'Napo', '150102'),
    ('Puerto Misahuallí', 'Napo', '150104'),
    
    # Pastaza
    ('Puyo', 'Pastaza', '160101'),
    ('Mera', 'Pastaza', '160102'),
    ('Santa Clara', 'Pastaza', '160103'),
    ('Arajuno', 'Pastaza', '160104'),
    
    # Pichincha
    ('Quito', 'Pichincha', '170101'),
    ('Cayambe', 'Pichincha', '170102'),
    ('Machachi', 'Pichincha', '170103'),
    ('Sangolquí', 'Pichincha', '170104'),
    ('Puembo', 'Pichincha', '170106'),
    
    # Santa Elena
    ('Santa Elena', 'Santa Elena', '240101'),
    ('La Libertad', 'Santa Elena', '240102'),
    ('Salinas', 'Santa Elena', '240103'),
    ('Olon', 'Santa Elena', '240104'),
    
    # Santo Domingo
    ('Santo Domingo', 'Santo Domingo de los Tsáchilas', '230101'),
    
    # Sucumbíos
    ('Nueva Loja', 'Sucumbíos', '210101'),
    ('Lago Agrio', 'Sucumbíos', '210102'),
    ('Cascales', 'Sucumbíos', '210103'),
    ('Putumayo', 'Sucumbíos', '210104'),
    
    # Tungurahua
    ('Ambato', 'Tungurahua', '180101'),
    ('Baños', 'Tungurahua', '180102'),
    ('Pelileo', 'Tungurahua', '180104'),
    ('Píllaro', 'Tungurahua', '180105'),
    
    # Orellana
    ('Puerto Francisco de Orellana', 'Orellana', '220101'),
    ('Coca', 'Orellana', '220102'),
    ('Joya de los Sachas', 'Orellana', '220103'),
]

print("\n" + "="*60)
print("IMPORTANDO CIUDADES DEL ECUADOR (LIVENSHOP)")
print("="*60)

created_prov_count = 0
created_ciu_count = 0
existing_ciu_count = 0

for nombre_ciu, nombre_prov, codigo in ciudades_ecuador:
    # 1. Obtener o crear provincia
    provincia_obj, created_prov = Provincia.objects.get_or_create(
        nombre=nombre_prov,
        defaults={'activa': True}
    )
    if created_prov:
        created_prov_count += 1
        
    # 2. Obtener o crear ciudad
    ciudad_obj, created_ciu = Ciudad.objects.get_or_create(
        nombre=nombre_ciu,
        provincia=provincia_obj,
        defaults={
            'codigo_postal': codigo,
            'activa': True
        }
    )
    
    if created_ciu:
        print(f"✓ Creada: {nombre_ciu:30} - {nombre_prov}")
        created_ciu_count += 1
    else:
        existing_ciu_count += 1

print("\n" + "="*60)
print(f"RESULTADO:")
print(f"  Provincias creadas: {created_prov_count}")
print(f"  Ciudades creadas: {created_ciu_count}")
print(f"  Ciudades existentes: {existing_ciu_count}")
print(f"  Total Provincias en la BD: {Provincia.objects.count()}")
print(f"  Total Ciudades en la BD: {Ciudad.objects.count()}")
print("="*60 + "\n")
