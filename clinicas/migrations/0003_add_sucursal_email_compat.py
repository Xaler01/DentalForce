"""No-op compatibility migration.

In the refactor branch we introduced a safeguard migration to add the
`email` column to `clinicas_sucursal`. However, the initial migration
already creates that column, so adding it again breaks clean database
creation (duplicate column). To keep migration numbering consistent while
avoiding duplicate DDL, we convert this migration into a no-op.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinicas', '0002_alter_sucursal_horario_apertura_and_more'),
    ]

    operations = []
