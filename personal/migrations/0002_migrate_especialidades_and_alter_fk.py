# Migration to copy especialidades from cit to clinicas and update references

from django.db import migrations, models
import django.db.models.deletion

def copy_especialidades(apps, schema_editor):
    """Copy especialidades from cit_especialidad to clinicas_especialidad"""
    # Get models
    CitEspecialidad = apps.get_model('cit', 'Especialidad')
    ClinicasEspecialidad = apps.get_model('clinicas', 'Especialidad')
    ComisionDentista = apps.get_model('personal', 'ComisionDentista')
    Dentista = apps.get_model('personal', 'Dentista')
    
    # Map old IDs to new IDs
    id_map = {}
    
    try:
        # Copy all especialidades from cit to clinicas
        for cit_esp in CitEspecialidad.objects.all():
            # Check if it already exists in clinicas
            try:
                clinicas_esp = ClinicasEspecialidad.objects.get(nombre=cit_esp.nombre)
                id_map[cit_esp.id] = clinicas_esp.id
            except ClinicasEspecialidad.DoesNotExist:
                # Create new one in clinicas
                clinicas_esp = ClinicasEspecialidad.objects.create(
                    nombre=cit_esp.nombre,
                    descripcion=getattr(cit_esp, 'descripcion', ''),
                    duracion=getattr(cit_esp, 'duracion', 30),
                    color=getattr(cit_esp, 'color', '#007bff'),
                    estado=cit_esp.estado,
                    uc=cit_esp.uc,
                    fc=cit_esp.fc,
                    fm=cit_esp.fm,
                    um=cit_esp.um,
                )
                id_map[cit_esp.id] = clinicas_esp.id
        
        # Update all dentista especialidades M2M to use clinicas especialidades
        for dentista in Dentista.objects.all():
            # Get old especialidades through M2M
            old_espec_ids = list(dentista.especialidades.values_list('id', flat=True))
            # Clear old M2M
            dentista.especialidades.clear()
            # Add mapped new ones
            for old_id in old_espec_ids:
                if old_id in id_map:
                    dentista.especialidades.add(id_map[old_id])
        
        # Update all comisiones to point to clinicas especialidades
        for comision in ComisionDentista.objects.all():
            if comision.especialidad_id in id_map:
                comision.especialidad_id = id_map[comision.especialidad_id]
                comision.save()
    
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()

def reverse_migration(apps, schema_editor):
    """Reverse migration"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('personal', '0001_initial'),
        ('clinicas', '0006_especialidad_cubiculo'),
    ]

    operations = [
        # First copy the data
        migrations.RunPython(copy_especialidades, reverse_migration),
        # Then alter the FK to point to clinicas
        migrations.AlterField(
            model_name='comisiondentista',
            name='especialidad',
            field=models.ForeignKey(help_text='Especialidad sobre la que se aplica la comisión', on_delete=django.db.models.deletion.CASCADE, related_name='comisiones', to='clinicas.especialidad', verbose_name='Especialidad'),
        ),
        migrations.AlterField(
            model_name='dentista',
            name='especialidades',
            field=models.ManyToManyField(help_text='Especialidades que practica el dentista', related_name='dentistas', to='clinicas.especialidad', verbose_name='Especialidades'),
        ),
    ]
