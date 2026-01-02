"""
Script para cargar fixtures de enfermedades con auditoría
SOOD-74: Carga de 10 categorías y 51 enfermedades
"""
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from django.contrib.auth.models import User
from enfermedades.models import CategoriaEnfermedad, Enfermedad

# Obtener usuario admin para auditoría
try:
    user_admin = User.objects.filter(is_superuser=True).first()
    if not user_admin:
        user_admin = User.objects.first()
    if not user_admin:
        print("⚠️  No hay usuarios en el sistema. Crea un superusuario primero.")
        exit(1)
except Exception as e:
    print(f"❌ Error obteniendo usuario: {e}")
    exit(1)

print(f"👤 Usuario para auditoría: {user_admin.username}")
print("=" * 60)

# Categorías
categorias_data = [
    {"id": 1, "nombre": "Cardiovascular", "descripcion": "Enfermedades del corazón y sistema circulatorio", "icono": "fa-heart", "color": "#dc3545", "orden": 1},
    {"id": 2, "nombre": "Endocrinológica", "descripcion": "Trastornos del sistema endocrino y metabolismo", "icono": "fa-heartbeat", "color": "#28a745", "orden": 2},
    {"id": 3, "nombre": "Respiratoria", "descripcion": "Enfermedades del sistema respiratorio", "icono": "fa-lungs", "color": "#17a2b8", "orden": 3},
    {"id": 4, "nombre": "Alérgica", "descripcion": "Alergias y reacciones inmunológicas", "icono": "fa-allergies", "color": "#ffc107", "orden": 4},
    {"id": 5, "nombre": "Hematológica", "descripcion": "Trastornos de la sangre y coagulación", "icono": "fa-tint", "color": "#6f42c1", "orden": 5},
    {"id": 6, "nombre": "Autoinmune", "descripcion": "Enfermedades autoinmunes y del sistema inmunológico", "icono": "fa-shield-virus", "color": "#fd7e14", "orden": 6},
    {"id": 7, "nombre": "Infecciosa", "descripcion": "Enfermedades infecciosas virales y bacterianas", "icono": "fa-virus", "color": "#e83e8c", "orden": 7},
    {"id": 8, "nombre": "Neurológica", "descripcion": "Trastornos del sistema nervioso", "icono": "fa-brain", "color": "#6c757d", "orden": 8},
    {"id": 9, "nombre": "Renal", "descripcion": "Enfermedades del sistema renal y urinario", "icono": "fa-prescription-bottle", "color": "#20c997", "orden": 9},
    {"id": 10, "nombre": "Otras", "descripcion": "Otras condiciones médicas relevantes", "icono": "fa-notes-medical", "color": "#6c757d", "orden": 10},
]

print("📋 Cargando Categorías...")
categorias_creadas = 0
for cat_data in categorias_data:
    cat, created = CategoriaEnfermedad.objects.update_or_create(
        id=cat_data['id'],
        defaults={
            'nombre': cat_data['nombre'],
            'descripcion': cat_data['descripcion'],
            'icono': cat_data['icono'],
            'color': cat_data['color'],
            'orden': cat_data['orden'],
            'estado': True,
            'uc': user_admin,
            'um': user_admin,
            'fc': timezone.now(),
            'fm': timezone.now(),
        }
    )
    if created:
        categorias_creadas += 1
        print(f"  ✅ {cat.nombre}")
    else:
        print(f"  ♻️  {cat.nombre} (actualizada)")

print(f"\n✅ {categorias_creadas} categorías creadas, {len(categorias_data) - categorias_creadas} actualizadas")
print("=" * 60)

# Enfermedades (51 en total)
enfermedades_data = [
    # Cardiovasculares (11)
    {"id": 1, "categoria_id": 1, "nombre": "Hipertensión Arterial", "nombre_cientifico": "Hipertensión Esencial", "codigo_cie10": "I10", 
     "descripcion": "Presión arterial elevada de forma crónica", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Evitar vasoconstrictores en exceso. Limitar epinefrina en anestésicos.",
     "precauciones": "Monitorear presión arterial antes de procedimientos. Sesiones cortas.",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 2, "categoria_id": 1, "nombre": "Infarto Agudo de Miocardio (IAM)", "nombre_cientifico": "Síndrome Coronario Agudo", "codigo_cie10": "I21",
     "descripcion": "Daño al músculo cardíaco por obstrucción coronaria", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "No realizar procedimientos electivos durante 6 meses post-IAM.",
     "precauciones": "Requiere autorización médica. Monitoreo continuo.",
     "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 3, "categoria_id": 1, "nombre": "Arritmia Cardíaca", "codigo_cie10": "I49", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Limitar vasoconstrictores.", "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 4, "categoria_id": 1, "nombre": "Insuficiencia Cardíaca", "codigo_cie10": "I50", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Evitar sobrecarga de líquidos.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 5, "categoria_id": 1, "nombre": "Angina de Pecho", "codigo_cie10": "I20", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Evitar estrés y procedimientos prolongados.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 6, "categoria_id": 1, "nombre": "Marcapasos o Desfibrilador", "codigo_cie10": "Z95.0", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Evitar electrocirugía.", "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 7, "categoria_id": 1, "nombre": "Endocarditis Infecciosa Previa", "codigo_cie10": "I33", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Requiere profilaxis antibiótica obligatoria.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 8, "categoria_id": 1, "nombre": "Valvulopatía Cardíaca", "codigo_cie10": "I35", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Requiere profilaxis antibiótica.", "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 9, "categoria_id": 1, "nombre": "Cardiopatía Congénita", "codigo_cie10": "Q24", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 10, "categoria_id": 1, "nombre": "Anticoagulación Oral", "codigo_cie10": "Z92.1", "nivel_riesgo": "ALTO",
     "contraindicaciones": "No suspender sin autorización médica.", "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 11, "categoria_id": 1, "nombre": "Accidente Cerebrovascular (ACV)", "codigo_cie10": "I64", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Esperar 6 meses post-ACV.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    # Endocrinológicas (7)
    {"id": 12, "categoria_id": 2, "nombre": "Diabetes Mellitus Tipo 1", "codigo_cie10": "E10", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Evitar si glicemia >250 mg/dL.", "genera_alerta_amarilla": True},
    
    {"id": 13, "categoria_id": 2, "nombre": "Diabetes Mellitus Tipo 2", "codigo_cie10": "E11", "nivel_riesgo": "MEDIO",
     "precauciones": "Control de glicemia. Mayor riesgo de infecciones.", "genera_alerta_amarilla": True},
    
    {"id": 14, "categoria_id": 2, "nombre": "Hipotiroidismo", "codigo_cie10": "E03", "nivel_riesgo": "MEDIO"},
    
    {"id": 15, "categoria_id": 2, "nombre": "Hipertiroidismo", "codigo_cie10": "E05", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Evitar vasoconstrictores si no controlado.", "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 16, "categoria_id": 2, "nombre": "Insuficiencia Suprarrenal", "codigo_cie10": "E27.1", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Requiere suplementación de corticoides.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 17, "categoria_id": 2, "nombre": "Síndrome de Cushing", "codigo_cie10": "E24", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 18, "categoria_id": 2, "nombre": "Obesidad Mórbida", "codigo_cie10": "E66.01", "nivel_riesgo": "MEDIO"},
    
    # Respiratorias (4)
    {"id": 19, "categoria_id": 3, "nombre": "Asma Bronquial", "codigo_cie10": "J45", "nivel_riesgo": "MEDIO",
     "contraindicaciones": "Evitar AINES si asma inducida.", "genera_alerta_amarilla": True},
    
    {"id": 20, "categoria_id": 3, "nombre": "EPOC", "codigo_cie10": "J44", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 21, "categoria_id": 3, "nombre": "Apnea Obstructiva del Sueño", "codigo_cie10": "G47.33", "nivel_riesgo": "MEDIO"},
    
    {"id": 22, "categoria_id": 3, "nombre": "Tuberculosis Activa", "codigo_cie10": "A15", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Posponer hasta 2 semanas de tratamiento.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    # Alérgicas (6)
    {"id": 23, "categoria_id": 4, "nombre": "Alergia a Penicilina", "codigo_cie10": "Z88.0", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Contraindicada amoxicilina y derivados.", "genera_alerta_roja": True},
    
    {"id": 24, "categoria_id": 4, "nombre": "Alergia a Anestésicos Locales", "codigo_cie10": "Z88.4", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Contraindicado anestésico identificado.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 25, "categoria_id": 4, "nombre": "Alergia al Látex", "codigo_cie10": "Z91.040", "nivel_riesgo": "ALTO",
     "contraindicaciones": "Evitar guantes y dique de látex.", "genera_alerta_roja": True},
    
    {"id": 26, "categoria_id": 4, "nombre": "Alergia a AINES", "codigo_cie10": "Z88.1", "nivel_riesgo": "MEDIO",
     "contraindicaciones": "Evitar ibuprofeno, aspirina.", "genera_alerta_amarilla": True},
    
    {"id": 27, "categoria_id": 4, "nombre": "Alergia a Metales (Níquel, Cromo)", "codigo_cie10": "L23.0", "nivel_riesgo": "BAJO"},
    
    {"id": 28, "categoria_id": 4, "nombre": "Reacción Anafiláctica Previa", "codigo_cie10": "T78.2", "nivel_riesgo": "CRITICO",
     "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    # Hematológicas (5)
    {"id": 29, "categoria_id": 5, "nombre": "Hemofilia", "codigo_cie10": "D66", "nivel_riesgo": "CRITICO",
     "contraindicaciones": "Evitar anestesia troncular si posible.", "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 30, "categoria_id": 5, "nombre": "Enfermedad de Von Willebrand", "codigo_cie10": "D68.0", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 31, "categoria_id": 5, "nombre": "Trombocitopenia", "codigo_cie10": "D69.6", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 32, "categoria_id": 5, "nombre": "Anemia Severa", "codigo_cie10": "D64.9", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 33, "categoria_id": 5, "nombre": "Leucemia", "codigo_cie10": "C95", "nivel_riesgo": "CRITICO",
     "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    # Autoinmunes (4)
    {"id": 34, "categoria_id": 6, "nombre": "VIH/SIDA", "codigo_cie10": "B20", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 35, "categoria_id": 6, "nombre": "Lupus Eritematoso Sistémico", "codigo_cie10": "M32", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 36, "categoria_id": 6, "nombre": "Artritis Reumatoide", "codigo_cie10": "M05", "nivel_riesgo": "MEDIO"},
    
    {"id": 37, "categoria_id": 6, "nombre": "Síndrome de Sjögren", "codigo_cie10": "M35.0", "nivel_riesgo": "BAJO"},
    
    # Infecciosas (3)
    {"id": 38, "categoria_id": 7, "nombre": "Hepatitis B Activa", "codigo_cie10": "B18.1", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 39, "categoria_id": 7, "nombre": "Hepatitis C", "codigo_cie10": "B18.2", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 40, "categoria_id": 7, "nombre": "Herpes Simple Recurrente", "codigo_cie10": "B00.1", "nivel_riesgo": "BAJO"},
    
    # Neurológicas (4)
    {"id": 41, "categoria_id": 8, "nombre": "Epilepsia", "codigo_cie10": "G40", "nivel_riesgo": "MEDIO",
     "genera_alerta_amarilla": True},
    
    {"id": 42, "categoria_id": 8, "nombre": "Enfermedad de Parkinson", "codigo_cie10": "G20", "nivel_riesgo": "MEDIO"},
    
    {"id": 43, "categoria_id": 8, "nombre": "Esclerosis Múltiple", "codigo_cie10": "G35", "nivel_riesgo": "MEDIO"},
    
    {"id": 44, "categoria_id": 8, "nombre": "Alzheimer / Demencia", "codigo_cie10": "G30", "nivel_riesgo": "BAJO"},
    
    # Renales (2)
    {"id": 45, "categoria_id": 9, "nombre": "Insuficiencia Renal Crónica", "codigo_cie10": "N18", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 46, "categoria_id": 9, "nombre": "Hemodiálisis", "codigo_cie10": "Z99.2", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    # Otras (5)
    {"id": 47, "categoria_id": 10, "nombre": "Embarazo", "codigo_cie10": "Z33.1", "nivel_riesgo": "MEDIO",
     "genera_alerta_amarilla": True},
    
    {"id": 48, "categoria_id": 10, "nombre": "Radioterapia en Cabeza/Cuello", "codigo_cie10": "Z92.3", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 49, "categoria_id": 10, "nombre": "Quimioterapia Activa", "codigo_cie10": "Z51.1", "nivel_riesgo": "CRITICO",
     "requiere_interconsulta": True, "genera_alerta_roja": True},
    
    {"id": 50, "categoria_id": 10, "nombre": "Bifosfonatos (Osteoporosis/Cáncer)", "codigo_cie10": "Z79.83", "nivel_riesgo": "ALTO",
     "requiere_interconsulta": True, "genera_alerta_amarilla": True},
    
    {"id": 51, "categoria_id": 10, "nombre": "Trastorno de Ansiedad / Fobia Dental", "codigo_cie10": "F41.9", "nivel_riesgo": "BAJO"},
]

print("🏥 Cargando Enfermedades (51 total)...")
enfermedades_creadas = 0
for enf_data in enfermedades_data:
    enf, created = Enfermedad.objects.update_or_create(
        id=enf_data['id'],
        defaults={
            'categoria_id': enf_data['categoria_id'],
            'nombre': enf_data['nombre'],
            'nombre_cientifico': enf_data.get('nombre_cientifico', ''),
            'codigo_cie10': enf_data.get('codigo_cie10', ''),
            'descripcion': enf_data.get('descripcion', ''),
            'nivel_riesgo': enf_data.get('nivel_riesgo', 'MEDIO'),
            'contraindicaciones': enf_data.get('contraindicaciones', ''),
            'precauciones': enf_data.get('precauciones', ''),
            'requiere_interconsulta': enf_data.get('requiere_interconsulta', False),
            'genera_alerta_roja': enf_data.get('genera_alerta_roja', False),
            'genera_alerta_amarilla': enf_data.get('genera_alerta_amarilla', False),
            'estado': True,
            'uc': user_admin,
            'um': user_admin,
            'fc': timezone.now(),
            'fm': timezone.now(),
        }
    )
    if created:
        enfermedades_creadas += 1
        print(f"  ✅ {enf.nombre} ({enf.nivel_riesgo})")

print(f"\n✅ {enfermedades_creadas} enfermedades creadas, {len(enfermedades_data) - enfermedades_creadas} actualizadas")
print("=" * 60)

# Resumen
print("\n📊 RESUMEN DE CARGA:")
print(f"  • Categorías: {CategoriaEnfermedad.objects.count()}")
print(f"  • Enfermedades: {Enfermedad.objects.count()}")
print(f"    - CRÍTICAS (🔴): {Enfermedad.objects.filter(nivel_riesgo='CRITICO').count()}")
print(f"    - ALTAS (🟠): {Enfermedad.objects.filter(nivel_riesgo='ALTO').count()}")
print(f"    - MEDIAS (🟡): {Enfermedad.objects.filter(nivel_riesgo='MEDIO').count()}")
print(f"    - BAJAS (🟢): {Enfermedad.objects.filter(nivel_riesgo='BAJO').count()}")
print(f"  • Requieren interconsulta: {Enfermedad.objects.filter(requiere_interconsulta=True).count()}")
print(f"  • Generan alerta ROJA: {Enfermedad.objects.filter(genera_alerta_roja=True).count()}")
print(f"  • Generan alerta AMARILLA: {Enfermedad.objects.filter(genera_alerta_amarilla=True).count()}")

print("\n🎉 SOOD-74 completado exitosamente!")
