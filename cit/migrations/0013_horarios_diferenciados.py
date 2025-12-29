# Generated manually for SOOD-48: Horarios diferenciados

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cit', '0012_clinica_logo_clinica_moneda_clinica_pais_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sucursal',
            name='sabado_horario_apertura',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Sábado - Hora de Apertura',
                help_text='Dejar vacío para usar el horario general'
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='sabado_horario_cierre',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Sábado - Hora de Cierre',
                help_text='Dejar vacío para usar el horario general'
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='domingo_horario_apertura',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Domingo - Hora de Apertura',
                help_text='Dejar vacío para usar el horario general'
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='domingo_horario_cierre',
            field=models.TimeField(
                blank=True,
                null=True,
                verbose_name='Domingo - Hora de Cierre',
                help_text='Dejar vacío para usar el horario general'
            ),
        ),
    ]
