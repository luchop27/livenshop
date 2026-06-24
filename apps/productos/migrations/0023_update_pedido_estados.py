from django.db import migrations, models


def migrate_estados(apps, schema_editor):
    Pedido = apps.get_model('productos', 'Pedido')
    estado_map = {
        'pendiente': 'en_proceso',
        'enviado': 'en_proceso',
        'entregado': 'pagado',
        'cancelado': 'anulado',
    }
    pedidos = Pedido.objects.filter(estado__in=list(estado_map.keys()))
    for pedido in pedidos:
        pedido.estado = estado_map[pedido.estado]
        pedido.save(update_fields=['estado'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0022_update_tiendaconfig_contacto'),
    ]

    operations = [
        migrations.RunPython(migrate_estados, noop),
        migrations.AlterField(
            model_name='pedido',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pagado', 'Pagado'),
                    ('en_proceso', 'En Proceso'),
                    ('anulado', 'Anulado'),
                ],
                default='en_proceso',
                max_length=20,
            ),
        ),
    ]
