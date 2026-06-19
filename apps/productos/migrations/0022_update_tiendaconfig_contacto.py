from django.db import migrations


def update_tienda_config(apps, schema_editor):
    TiendaConfig = apps.get_model('productos', 'TiendaConfig')
    config = TiendaConfig.objects.first()
    if config:
        config.telefono = '0995443335'
        config.email = 'liven_concept@outlook.com'
        config.direccion = 'C.C Del Portal'
        config.horario_apertura = 'Lun-Vier 10am-8pm | Sáb 9am-7pm'
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0021_productodestacadomarca'),
    ]

    operations = [
        migrations.RunPython(update_tienda_config, migrations.RunPython.noop),
    ]
