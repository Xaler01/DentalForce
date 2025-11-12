"""
Script para crear una cita de ejemplo en el sistema.
Ejecutar con: python manage.py shell < crear_cita_ejemplo.py
"""

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from cit.models import Cita, Clinica, Sucursal, Dentista, Paciente, Especialidad, Cubiculo

# Obtener o crear usuario de sistema
try:
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@powerdent.com', 'admin')
        print("✓ Usuario admin creado")
    else:
        print(f"✓ Usando usuario: {user.username}")
except:
    user = User.objects.first()
    print(f"✓ Usando primer usuario: {user.username}")

# Verificar si ya existe una cita de ejemplo
citas_existentes = Cita.objects.filter(observaciones__contains='Cita de ejemplo').count()
if citas_existentes > 0:
    print(f"⚠ Ya existen {citas_existentes} citas de ejemplo en el sistema")
    print("  Si deseas crear más, puedes ejecutar este script nuevamente")
else:
    # Obtener el primer paciente, dentista, especialidad y cubículo
    try:
        paciente = Paciente.objects.first()
        dentista = Dentista.objects.first()
        especialidad = Especialidad.objects.first()
        cubiculo = Cubiculo.objects.first()
        
        if not all([paciente, dentista, especialidad, cubiculo]):
            print("✗ ERROR: Faltan datos básicos (paciente, dentista, especialidad o cubículo)")
            print("  Debes crear estos registros primero desde el sistema")
        else:
            # Crear cita para mañana a las 10:00
            fecha_cita = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            cita = Cita.objects.create(
                paciente=paciente,
                dentista=dentista,
                especialidad=especialidad,
                cubiculo=cubiculo,
                fecha_hora=fecha_cita,
                duracion=60,
                estado=Cita.ESTADO_CONFIRMADA,
                observaciones='Cita de ejemplo para testing - Control de rutina',
                uc=user,
                um=user.id
            )
            
            print("\n" + "="*60)
            print("✓ CITA DE EJEMPLO CREADA EXITOSAMENTE")
            print("="*60)
            print(f"  ID: {cita.id}")
            print(f"  Paciente: {cita.paciente.get_nombre_completo()}")
            print(f"  Dentista: {cita.dentista}")
            print(f"  Especialidad: {cita.especialidad.nombre}")
            print(f"  Fecha/Hora: {cita.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
            print(f"  Duración: {cita.duracion} minutos")
            print(f"  Estado: {cita.get_estado_display()}")
            print(f"  Cubículo: {cita.cubiculo.nombre}")
            print("="*60)
            print(f"\n👉 Puedes verla en: http://localhost:8000/cit/calendario/")
            print(f"👉 O en detalle: http://localhost:8000/cit/citas/{cita.id}/\n")
            
    except Exception as e:
        print(f"✗ ERROR al crear cita: {str(e)}")
        import traceback
        traceback.print_exc()
