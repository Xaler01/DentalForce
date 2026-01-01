"""
Script para crear la especialidad "Odontología General" y asignarla a todos los dentistas existentes.
Ejecutar con: python manage.py shell < create_odontologia_general.py
"""
from cit.models import Especialidad, Dentista
from django.contrib.auth.models import User

# Obtener un usuario admin (el primero que sea superuser, o el primero en general)
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.first()

if not user:
    print("❌ No hay usuarios en el sistema. Por favor crea un usuario primero.")
    exit(1)

# Crear la especialidad "Odontología General" si no existe
try:
    odontologia_general = Especialidad.objects.get(nombre='Odontología General')
    created = False
except Especialidad.DoesNotExist:
    odontologia_general = Especialidad.objects.create(
        nombre='Odontología General',
        descripcion='Odontología General - Servicios básicos de odontología, resinas y tratamientos de emergencia',
        duracion_default=30,
        color_calendario='#2ecc71',  # Verde
        estado=True,
        uc=user
    )
    created = True

if created:
    print(f"✅ Especialidad 'Odontología General' creada exitosamente")
else:
    print(f"ℹ️  Especialidad 'Odontología General' ya existía")

# Asignar la especialidad a todos los dentistas que no la tengan
dentistas_sin_odontologia = Dentista.objects.filter(estado=True).exclude(especialidades=odontologia_general)
count = dentistas_sin_odontologia.count()

if count > 0:
    for dentista in dentistas_sin_odontologia:
        dentista.especialidades.add(odontologia_general)
    print(f"✅ Asignada 'Odontología General' a {count} dentistas")
else:
    print(f"ℹ️  Todos los dentistas ya tienen 'Odontología General'")
    
print("\n✅ Proceso completado exitosamente")
