from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portafolio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Servicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, verbose_name='Título')),
                ('descripcion', models.TextField(help_text='Separa párrafos con una línea en blanco.', verbose_name='Descripción')),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='servicios/', verbose_name='Imagen')),
                ('lado_imagen', models.CharField(
                    choices=[('izquierda', 'Imagen a la izquierda'), ('derecha', 'Imagen a la derecha')],
                    default='izquierda',
                    max_length=10,
                    verbose_name='Posición de la imagen',
                )),
                ('posicion', models.PositiveIntegerField(default=0, verbose_name='Posición')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Servicio',
                'verbose_name_plural': 'Servicios',
                'ordering': ['posicion'],
            },
        ),
    ]
