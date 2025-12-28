"""Add missing `email` field to Sucursal for environments with out-of-sync schema.

This migration is a safety migration: some development databases may have
the `clinicas_sucursal` table without the `email` column even though earlier
migrations declared it. Creating this migration ensures the column exists.

If your DB already contains the `email` column, applying this migration will
raise an error; in that case revert and investigate schema/state.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinicas', '0002_alter_sucursal_horario_apertura_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sucursal',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email', help_text='Email de contacto de la sucursal'),
        ),
    ]
