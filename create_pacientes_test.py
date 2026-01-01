"""
Script para crear 20 pacientes de prueba para validar la búsqueda.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from pacientes.models import Paciente
from django.contrib.auth.models import User
from datetime import date
import random

# Obtener un usuario para crear los pacientes
user = User.objects.first()
if not user:
    print("❌ No hay usuarios en la base de datos")
    exit(1)

# Lista de nombres y apellidos de Ecuador
nombres_masculinos = ['Juan', 'Carlos', 'José', 'Luis', 'Miguel', 'Jorge', 'Pedro', 'Fernando', 'Diego', 'Andrés']
nombres_femeninos = ['María', 'Ana', 'Carmen', 'Lucía', 'Rosa', 'Patricia', 'Laura', 'Sofía', 'Gabriela', 'Isabella']
apellidos = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Ramírez',
             'Torres', 'Flores', 'Vásquez', 'Morales', 'Jiménez', 'Herrera', 'Medina', 'Castro', 'Vargas', 'Ortiz']

# Generar 20 pacientes
pacientes_creados = 0

print("\n🏥 Creando pacientes de prueba...")
print("=" * 60)

for i in range(1, 21):
    # Alternar entre masculino y femenino
    genero = 'M' if i % 2 == 0 else 'F'
    nombres = random.choice(nombres_masculinos if genero == 'M' else nombres_femeninos)
    apellido1 = random.choice(apellidos)
    apellido2 = random.choice(apellidos)
    
    # Generar cédula ecuatoriana (10 dígitos)
    cedula = f"{random.randint(1000000000, 1999999999)}"
    
    # Verificar que no exista
    if Paciente.objects.filter(cedula=cedula).exists():
        cedula = None  # Si existe, crear sin cédula
    
    # Generar fecha de nacimiento (entre 18 y 80 años)
    year = random.randint(1944, 2006)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    fecha_nacimiento = date(year, month, day)
    
    # Generar teléfono ecuatoriano
    telefono = f"09{random.randint(10000000, 99999999)}"
    
    # Ciudades de Ecuador
    ciudades = ['Quito', 'Guayaquil', 'Cuenca', 'Ambato', 'Manta', 'Machala', 'Loja', 'Portoviejo', 'Riobamba', 'Ibarra']
    ciudad = random.choice(ciudades)
    direccion = f"Av. Principal #{random.randint(100, 999)}, {ciudad}"
    
    # Tipos de sangre
    tipos_sangre = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    tipo_sangre = random.choice(tipos_sangre)
    
    try:
        paciente = Paciente.objects.create(
            nombres=nombres,
            apellidos=f"{apellido1} {apellido2}",
            cedula=cedula,
            fecha_nacimiento=fecha_nacimiento,
            genero=genero,
            telefono=telefono,
            direccion=direccion,
            tipo_sangre=tipo_sangre,
            uc=user
        )
        pacientes_creados += 1
        print(f"✅ {pacientes_creados:2d}. {paciente.nombres} {paciente.apellidos} - {paciente.cedula or 'Sin cédula'}")
    except Exception as e:
        print(f"❌ Error al crear paciente {i}: {e}")

print("=" * 60)
print(f"\n✨ Se crearon {pacientes_creados} pacientes de prueba exitosamente")
print(f"📊 Total de pacientes en la base de datos: {Paciente.objects.count()}\n")
