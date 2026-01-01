"""Crear la especialidad 'Diagnóstico' y asignarla a todos los dentistas."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from django.contrib.auth import get_user_model
from cit.models import Dentista, Especialidad

User = get_user_model()

# Obtener un usuario (idealmente admin) para setear como creador
uc = User.objects.filter(is_superuser=True).first() or User.objects.first()

print("\n🏥 Creando/actualizando especialidad Diagnóstico...")

# Crear o actualizar la especialidad Diagnóstico
diagnostico, created = Especialidad.objects.get_or_create(
    nombre='Diagnóstico',
    defaults={
        'descripcion': 'Evaluación diagnóstica inicial y seguimiento clínico',
        'duracion_default': 30,
        'color_calendario': '#8e44ad',
        'estado': True,
        'uc': uc,
    }
)

if not created:
    diagnostico.descripcion = diagnostico.descripcion or 'Evaluación diagnóstica inicial y seguimiento clínico'
    diagnostico.duracion_default = diagnostico.duracion_default or 30
    diagnostico.color_calendario = diagnostico.color_calendario or '#8e44ad'
    diagnostico.estado = True
    if uc and not diagnostico.uc:
        diagnostico.uc = uc
    diagnostico.save()
    print("✅ Especialidad Diagnóstico ya existía, se aseguraron campos base")
else:
    print("✅ Especialidad Diagnóstico creada")

# Asignar a todos los dentistas
asignados = 0
for dentista in Dentista.objects.all():
    if not dentista.especialidades.filter(pk=diagnostico.pk).exists():
        dentista.especialidades.add(diagnostico)
        asignados += 1

print(f"✨ Diagnóstico asignado a {asignados} dentistas nuevos")
print(f"📊 Total dentistas con Diagnóstico: {Dentista.objects.filter(especialidades=diagnostico).count()}\n")
