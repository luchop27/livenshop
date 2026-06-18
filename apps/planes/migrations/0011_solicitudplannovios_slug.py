from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    SolicitudPlanNovios = apps.get_model('planes', 'SolicitudPlanNovios')
    for sol in SolicitudPlanNovios.objects.all():
        base = sol.nombres_novios or ''
        if sol.apellidos_novios:
            base = f"{base} y {sol.apellidos_novios}"
        base_slug = slugify(base) or f'pareja-{sol.pk}'
        slug = base_slug
        n = 2
        while SolicitudPlanNovios.objects.filter(slug=slug).exclude(pk=sol.pk).exists():
            slug = f"{base_slug}-{n}"
            n += 1
        sol.slug = slug
        sol.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('planes', '0010_solicitudplannovios_monto_minimo_regalo'),
    ]

    operations = [
        # 1. Agregar el campo SIN unique (permite vacíos temporales)
        migrations.AddField(
            model_name='solicitudplannovios',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=300, verbose_name='Slug (URL amigable)'),
            preserve_default=False,
        ),
        # 2. Llenar los slugs de registros existentes
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        # 3. Ahora sí aplicar unique=True
        migrations.AlterField(
            model_name='solicitudplannovios',
            name='slug',
            field=models.SlugField(blank=True, max_length=300, unique=True, verbose_name='Slug (URL amigable)'),
        ),
    ]
