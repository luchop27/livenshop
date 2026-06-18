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
        # 1. Agregar columna sin unique (el índice _like se crea aquí automáticamente)
        migrations.AddField(
            model_name='solicitudplannovios',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=300, verbose_name='Slug (URL amigable)'),
            preserve_default=False,
        ),
        # 2. Llenar slugs de registros existentes
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        # 3. Agregar UNIQUE por SQL directo — no recrea el índice _like (evita DuplicateTable)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE planes_solicitudplannovios
                        ADD CONSTRAINT planes_solicitudplannovios_slug_uniq UNIQUE (slug);
                    """,
                    reverse_sql="""
                        ALTER TABLE planes_solicitudplannovios
                        DROP CONSTRAINT IF EXISTS planes_solicitudplannovios_slug_uniq;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='solicitudplannovios',
                    name='slug',
                    field=models.SlugField(
                        blank=True, max_length=300, unique=True,
                        verbose_name='Slug (URL amigable)'
                    ),
                ),
            ],
        ),
    ]
