#!/usr/bin/env python
"""
Script para cargar 51 procedimientos odontológicos iniciales en PowerDent.
Corre como: python manage.py shell < procedimientos/load_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from procedimientos.models import ProcedimientoOdontologico
from django.contrib.auth.models import User

# Obtener usuario admin
try:
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ No se encontró usuario admin. Crea uno primero.")
        exit(1)
except:
    print("❌ Error al obtener usuario admin.")
    exit(1)

# Datos de procedimientos
PROCEDIMIENTOS = [
    ("DIA-EX001", "D0150", "Examen clínico completo", "Evaluación integral del paciente nuevo con historia clínica completa", "DIAGNOSTICO", 30, False, False),
    ("DIA-EX002", "D0120", "Examen periódico", "Control de paciente establecido", "DIAGNOSTICO", 15, False, False),
    ("DIA-RX001", "D0220", "Radiografía periapical", "Radiografía de un solo diente", "DIAGNOSTICO", 5, False, False),
    ("DIA-RX002", "D0330", "Radiografía panorámica", "Radiografía completa de maxilares", "DIAGNOSTICO", 15, False, False),
    ("DIA-RX003", "D0270", "Radiografía bite-wing", "Radiografía interproximal", "DIAGNOSTICO", 5, False, False),
    ("PRE-LIM001", "D1110", "Limpieza dental (profilaxis)", "Limpieza de adulto", "PREVENTIVA", 45, False, False),
    ("PRE-LIM002", "D1120", "Limpieza dental infantil", "Limpieza pediátrica", "PREVENTIVA", 30, False, False),
    ("PRE-FLU001", "D1206", "Aplicación de flúor", "Barniz de flúor", "PREVENTIVA", 10, False, False),
    ("PRE-SEL001", "D1351", "Sellante por diente", "Sellante de fosas y fisuras", "PREVENTIVA", 15, False, True),
    ("PRE-EDU001", "D1330", "Educación en higiene oral", "Instrucción de cepillado", "PREVENTIVA", 20, False, False),
    ("RES-OBT001", "D2140", "Obturación 1 superficie", "Resina/amalgama simple", "RESTAURATIVA", 30, True, True),
    ("RES-OBT002", "D2150", "Obturación 2 superficies", "Resina/amalgama compuesta", "RESTAURATIVA", 45, True, True),
    ("RES-OBT003", "D2160", "Obturación 3 superficies", "Resina/amalgama compleja", "RESTAURATIVA", 60, True, True),
    ("RES-OBT004", "D2161", "Obturación 4+ superficies", "Resina/amalgama extensa", "RESTAURATIVA", 75, True, True),
    ("RES-REC001", "D2330", "Reconstrucción dental", "Reconstrucción con resina", "RESTAURATIVA", 90, True, True),
    ("RES-INC001", "D2542", "Incrustación (Onlay)", "Restauración indirecta", "RESTAURATIVA", 120, True, True),
    ("END-CON001", "D3310", "Endodoncia unirradicular", "Conducto anterior", "ENDODONCIA", 60, True, True),
    ("END-CON002", "D3320", "Endodoncia birradicular", "Conducto premolar", "ENDODONCIA", 90, True, True),
    ("END-CON003", "D3330", "Endodoncia trirradicular", "Conducto molar", "ENDODONCIA", 120, True, True),
    ("END-RET001", "D3346", "Retratamiento unirradicular", "Repetir endodoncia", "ENDODONCIA", 90, True, True),
    ("END-API001", "D3410", "Apicectomía", "Cirugía apical", "ENDODONCIA", 60, True, True),
    ("PER-RAS001", "D4341", "Raspado y alisado (cuadrante)", "Limpieza profunda", "PERIODONCIA", 45, True, False),
    ("PER-CUR001", "D4210", "Curetaje periodontal", "Por cuadrante", "PERIODONCIA", 30, True, False),
    ("PER-GIN001", "D4210", "Gingivectomía (por diente)", "Eliminación de tejido", "PERIODONCIA", 20, True, False),
    ("PER-INJ001", "D4270", "Injerto gingival", "Cirugía de encía", "PERIODONCIA", 120, True, False),
    ("CIR-EXT001", "D7140", "Extracción simple", "Extracción no complicada", "CIRUGIA", 20, True, True),
    ("CIR-EXT002", "D7210", "Extracción quirúrgica", "Requiere colgajo", "CIRUGIA", 45, True, True),
    ("CIR-EXT003", "D7240", "Extracción muela del juicio", "Tercer molar impactado", "CIRUGIA", 60, True, True),
    ("CIR-ALV001", "D7310", "Alveoloplastia", "Regularización de hueso", "CIRUGIA", 30, True, True),
    ("CIR-BIO001", "D7285", "Biopsia de tejido oral", "Toma de muestra", "CIRUGIA", 30, True, False),
    ("PRO-COR001", "D2750", "Corona metal-porcelana", "Corona PFM", "PROSTODONCIA", 60, True, True),
    ("PRO-COR002", "D2740", "Corona porcelana pura", "Corona cerámica", "PROSTODONCIA", 60, True, True),
    ("PRO-COR003", "D2740", "Corona circonio", "Corona estética", "PROSTODONCIA", 60, True, True),
    ("PRO-PUE001", "D6240", "Puente 3 unidades", "Puente fijo", "PROSTODONCIA", 90, True, True),
    ("PRO-DEN001", "D5110", "Dentadura completa", "Prótesis total", "PROSTODONCIA", 180, False, True),
    ("PRO-DEN002", "D5211", "Dentadura parcial", "Prótesis removible", "PROSTODONCIA", 120, False, True),
    ("IMP-COL001", "D6010", "Colocación de implante", "Implante endoóseo", "IMPLANTES", 90, True, True),
    ("IMP-PIL001", "D6056", "Pilar (abutment)", "Conector de implante", "IMPLANTES", 30, False, True),
    ("IMP-COR001", "D6058", "Corona sobre implante", "Restauración final", "IMPLANTES", 60, False, True),
    ("IMP-INJ001", "D7953", "Injerto óseo", "Regeneración ósea", "IMPLANTES", 120, True, False),
    ("ORT-EVA001", "D8660", "Evaluación ortodóntica", "Estudio inicial", "ORTODONCIA", 45, False, False),
    ("ORT-BRA001", "D8080", "Brackets metálicos", "Aparatología fija", "ORTODONCIA", 120, False, True),
    ("ORT-BRA002", "D8080", "Brackets estéticos", "Cerámica/zafiro", "ORTODONCIA", 120, False, True),
    ("ORT-CON001", "D8670", "Control mensual", "Ajuste de aparatos", "ORTODONCIA", 20, False, True),
    ("ORT-RET001", "D8680", "Retenedor", "Post-tratamiento", "ORTODONCIA", 30, False, True),
    ("URG-DOL001", "D9110", "Atención por dolor", "Urgencia dental", "URGENCIAS", 30, True, False),
    ("URG-DRE001", "D7510", "Drenaje de absceso", "Urgencia infección", "URGENCIAS", 30, True, False),
    ("URG-CEM001", "D6930", "Recementación corona/puente", "Urgencia restauración", "URGENCIAS", 20, False, False),
    ("URG-REP001", "D2940", "Reparación provisional", "Restauración temporal", "URGENCIAS", 20, False, False),
    ("OTR-BLA001", "D9972", "Blanqueamiento dental", "Por sesión", "OTROS", 60, False, False),
    ("OTR-FER001", "D9944", "Férula oclusal", "Para bruxismo", "OTROS", 30, False, False),
]

print("\n" + "="*80)
print("📋 CARGANDO CATÁLOGO DE PROCEDIMIENTOS ODONTOLÓGICOS")
print("="*80 + "\n")

created_count = 0
skipped_count = 0

for codigo, codigo_cdt, nombre, descripcion, categoria, duracion, requiere_anestesia, afecta_odontograma in PROCEDIMIENTOS:
    # Verificar si ya existe
    if ProcedimientoOdontologico.objects.filter(codigo=codigo).exists():
        print(f"⏭️  {codigo}: {nombre} (YA EXISTE)")
        skipped_count += 1
        continue
    
    # Crear procedimiento
    proc = ProcedimientoOdontologico.objects.create(
        codigo=codigo,
        codigo_cdt=codigo_cdt,
        nombre=nombre,
        descripcion=descripcion,
        categoria=categoria,
        duracion_estimada=duracion,
        requiere_anestesia=requiere_anestesia,
        afecta_odontograma=afecta_odontograma,
        estado=True,
        uc=admin_user
    )
    print(f"✅ {codigo}: {nombre}")
    created_count += 1

print("\n" + "="*80)
print(f"📊 RESUMEN")
print(f"   ✅ Procedimientos creados: {created_count}")
print(f"   ⏭️  Procedimientos existentes: {skipped_count}")
print(f"   📈 Total en catálogo: {ProcedimientoOdontologico.objects.count()}")
print("="*80 + "\n")

print("✨ ¡Catálogo de procedimientos cargado exitosamente!")
print("   Próximo paso: Configurar precios por clínica en admin Django")
print(f"   URL: http://localhost:8000/admin/procedimientos/")
