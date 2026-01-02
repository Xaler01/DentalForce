"""
Comando Django para cargar fixtures de enfermedades
SOOD-74: Carga 10 categorías + 51 enfermedades
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from enfermedades.models import CategoriaEnfermedad, Enfermedad


class Command(BaseCommand):
    help = 'Carga las 10 categorías y 51 enfermedades predefinidas'

    def handle(self, *args, **options):
        user_admin = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user_admin:
            self.stdout.write(self.style.ERROR('No hay usuarios. Crea un superusuario primero.'))
            return

        self.stdout.write(f'👤 Usuario auditoría: {user_admin.username}')
        self.stdout.write('=' * 60)

        categorias = [
            (1, "Cardiovascular", "Enfermedades del corazón y sistema circulatorio", "fa-heart", "#dc3545", 1),
            (2, "Endocrinológica", "Trastornos del sistema endocrino y metabolismo", "fa-heartbeat", "#28a745", 2),
            (3, "Respiratoria", "Enfermedades del sistema respiratorio", "fa-lungs", "#17a2b8", 3),
            (4, "Alérgica", "Alergias y reacciones inmunológicas", "fa-allergies", "#ffc107", 4),
            (5, "Hematológica", "Trastornos de la sangre y coagulación", "fa-tint", "#6f42c1", 5),
            (6, "Autoinmune", "Enfermedades autoinmunes y del sistema inmunológico", "fa-shield-virus", "#fd7e14", 6),
            (7, "Infecciosa", "Enfermedades infecciosas virales y bacterianas", "fa-virus", "#e83e8c", 7),
            (8, "Neurológica", "Trastornos del sistema nervioso", "fa-brain", "#6c757d", 8),
            (9, "Renal", "Enfermedades del sistema renal y urinario", "fa-prescription-bottle", "#20c997", 9),
            (10, "Otras", "Otras condiciones médicas relevantes", "fa-notes-medical", "#6c757d", 10),
        ]

        self.stdout.write('📋 Cargando Categorías...')
        for pk, nombre, desc, icono, color, orden in categorias:
            try:
                obj = CategoriaEnfermedad.objects.get(id=pk)
                obj.nombre = nombre
                obj.descripcion = desc
                obj.icono = icono
                obj.color = color
                obj.orden = orden
                obj.um = user_admin.id
                obj.save()
                self.stdout.write(f'  ♻️  {nombre} (actualizada)')
            except CategoriaEnfermedad.DoesNotExist:
                CategoriaEnfermedad.objects.create(
                    id=pk,
                    nombre=nombre,
                    descripcion=desc,
                    icono=icono,
                    color=color,
                    orden=orden,
                    uc=user_admin,
                    um=user_admin.id,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✅ {nombre}'))

        total_cat = CategoriaEnfermedad.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ {total_cat} categorías en sistema'))
        self.stdout.write('=' * 60)

        enfermedades = [
            (1, 1, "Hipertensión Arterial", "I10", "ALTO", "Evitar vasoconstrictores en exceso.", True, True),
            (2, 1, "Infarto Agudo de Miocardio (IAM)", "I21", "CRITICO", "No procedimientos 6 meses post-IAM.", True, True),
            (3, 1, "Arritmia Cardíaca", "I49", "ALTO", "Limitar vasoconstrictores.", True, True),
            (4, 1, "Insuficiencia Cardíaca", "I50", "CRITICO", "Evitar sobrecarga de líquidos.", True, True),
            (5, 1, "Angina de Pecho", "I20", "CRITICO", "Evitar estrés prolongado.", True, True),
            (6, 1, "Marcapasos o Desfibrilador", "Z95.0", "ALTO", "Evitar electrocirugía.", True, True),
            (7, 1, "Endocarditis Infecciosa Previa", "I33", "CRITICO", "Profilaxis antibiótica obligatoria.", True, True),
            (8, 1, "Valvulopatía Cardíaca", "I35", "ALTO", "Requiere profilaxis antibiótica.", True, True),
            (9, 1, "Cardiopatía Congénita", "Q24", "ALTO", "", True, True),
            (10, 1, "Anticoagulación Oral", "Z92.1", "ALTO", "No suspender sin autorización.", True, True),
            (11, 1, "Accidente Cerebrovascular (ACV)", "I64", "CRITICO", "Esperar 6 meses post-ACV.", True, True),
            (12, 2, "Diabetes Mellitus Tipo 1", "E10", "ALTO", "Evitar si glicemia >250.", False, True),
            (13, 2, "Diabetes Mellitus Tipo 2", "E11", "MEDIO", "Mayor riesgo de infecciones.", False, True),
            (14, 2, "Hipotiroidismo", "E03", "MEDIO", "", False, False),
            (15, 2, "Hipertiroidismo", "E05", "ALTO", "Evitar vasoconstrictores si no controlado.", True, True),
            (16, 2, "Insuficiencia Suprarrenal", "E27.1", "CRITICO", "Requiere suplementación corticoides.", True, True),
            (17, 2, "Síndrome de Cushing", "E24", "ALTO", "", True, True),
            (18, 2, "Obesidad Mórbida", "E66.01", "MEDIO", "", False, False),
            (19, 3, "Asma Bronquial", "J45", "MEDIO", "Evitar AINES si asma inducida.", False, True),
            (20, 3, "EPOC", "J44", "ALTO", "", True, True),
            (21, 3, "Apnea Obstructiva del Sueño", "G47.33", "MEDIO", "", False, False),
            (22, 3, "Tuberculosis Activa", "A15", "CRITICO", "Posponer hasta 2 sem tratamiento.", True, True),
            (23, 4, "Alergia a Penicilina", "Z88.0", "ALTO", "Contraindicada amoxicilina.", False, True),
            (24, 4, "Alergia a Anestésicos Locales", "Z88.4", "CRITICO", "Contraindicado anestésico identificado.", True, True),
            (25, 4, "Alergia al Látex", "Z91.040", "ALTO", "Evitar guantes de látex.", False, True),
            (26, 4, "Alergia a AINES", "Z88.1", "MEDIO", "Evitar ibuprofeno, aspirina.", False, True),
            (27, 4, "Alergia a Metales (Níquel, Cromo)", "L23.0", "BAJO", "", False, False),
            (28, 4, "Reacción Anafiláctica Previa", "T78.2", "CRITICO", "Tener kit de anafilaxia.", True, True),
            (29, 5, "Hemofilia", "D66", "CRITICO", "Evitar anestesia troncular.", True, True),
            (30, 5, "Enfermedad de Von Willebrand", "D68.0", "ALTO", "", True, True),
            (31, 5, "Trombocitopenia", "D69.6", "ALTO", "", True, True),
            (32, 5, "Anemia Severa", "D64.9", "ALTO", "", True, True),
            (33, 5, "Leucemia", "C95", "CRITICO", "", True, True),
            (34, 6, "VIH/SIDA", "B20", "ALTO", "", True, True),
            (35, 6, "Lupus Eritematoso Sistémico", "M32", "ALTO", "", True, True),
            (36, 6, "Artritis Reumatoide", "M05", "MEDIO", "", False, False),
            (37, 6, "Síndrome de Sjögren", "M35.0", "BAJO", "", False, False),
            (38, 7, "Hepatitis B Activa", "B18.1", "ALTO", "", True, True),
            (39, 7, "Hepatitis C", "B18.2", "ALTO", "", True, True),
            (40, 7, "Herpes Simple Recurrente", "B00.1", "BAJO", "", False, False),
            (41, 8, "Epilepsia", "G40", "MEDIO", "", False, True),
            (42, 8, "Enfermedad de Parkinson", "G20", "MEDIO", "", False, False),
            (43, 8, "Esclerosis Múltiple", "G35", "MEDIO", "", False, False),
            (44, 8, "Alzheimer / Demencia", "G30", "BAJO", "", False, False),
            (45, 9, "Insuficiencia Renal Crónica", "N18", "ALTO", "", True, True),
            (46, 9, "Hemodiálisis", "Z99.2", "ALTO", "No día de diálisis.", True, True),
            (47, 10, "Embarazo", "Z33.1", "MEDIO", "", False, True),
            (48, 10, "Radioterapia en Cabeza/Cuello", "Z92.3", "ALTO", "", True, True),
            (49, 10, "Quimioterapia Activa", "Z51.1", "CRITICO", "", True, True),
            (50, 10, "Bifosfonatos (Osteoporosis/Cáncer)", "Z79.83", "ALTO", "", True, True),
            (51, 10, "Trastorno de Ansiedad / Fobia Dental", "F41.9", "BAJO", "", False, False),
        ]

        self.stdout.write('🏥 Cargando Enfermedades (51 total)...')
        for pk, cat_id, nombre, cie10, riesgo, contraindicaciones, interconsulta, alerta in enfermedades:
            alerta_roja = alerta and riesgo == "CRITICO"
            alerta_amarilla = alerta and riesgo in ["ALTO", "MEDIO"]
            try:
                obj = Enfermedad.objects.get(id=pk)
                obj.categoria_id = cat_id
                obj.nombre = nombre
                obj.codigo_cie10 = cie10
                obj.nivel_riesgo = riesgo
                obj.contraindicaciones = contraindicaciones
                obj.requiere_interconsulta = interconsulta
                obj.genera_alerta_roja = alerta_roja
                obj.genera_alerta_amarilla = alerta_amarilla
                obj.um = user_admin.id
                obj.save()
            except Enfermedad.DoesNotExist:
                Enfermedad.objects.create(
                    id=pk,
                    categoria_id=cat_id,
                    nombre=nombre,
                    codigo_cie10=cie10,
                    nivel_riesgo=riesgo,
                    contraindicaciones=contraindicaciones,
                    requiere_interconsulta=interconsulta,
                    genera_alerta_roja=alerta_roja,
                    genera_alerta_amarilla=alerta_amarilla,
                    uc=user_admin,
                    um=user_admin.id,
                )
                emoji = '🔴' if riesgo == 'CRITICO' else '🟠' if riesgo == 'ALTO' else '🟡' if riesgo == 'MEDIO' else '🟢'
                self.stdout.write(f'  ✅ {emoji} {nombre}')

        total_enf = Enfermedad.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✅ {total_enf} enfermedades en sistema'))
        self.stdout.write('=' * 60)

        self.stdout.write('\n📊 RESUMEN:')
        self.stdout.write(f'  • Categorías: {CategoriaEnfermedad.objects.count()}')
        self.stdout.write(f'  • Enfermedades: {Enfermedad.objects.count()}')
        self.stdout.write(f'    - 🔴 CRÍTICAS: {Enfermedad.objects.filter(nivel_riesgo="CRITICO").count()}')
        self.stdout.write(f'    - 🟠 ALTAS: {Enfermedad.objects.filter(nivel_riesgo="ALTO").count()}')
        self.stdout.write(f'    - 🟡 MEDIAS: {Enfermedad.objects.filter(nivel_riesgo="MEDIO").count()}')
        self.stdout.write(f'    - 🟢 BAJAS: {Enfermedad.objects.filter(nivel_riesgo="BAJO").count()}')
        self.stdout.write(f'  • Requieren interconsulta: {Enfermedad.objects.filter(requiere_interconsulta=True).count()}')
        self.stdout.write(f'  • Generan alerta ROJA: {Enfermedad.objects.filter(genera_alerta_roja=True).count()}')
        self.stdout.write(f'  • Generan alerta AMARILLA: {Enfermedad.objects.filter(genera_alerta_amarilla=True).count()}')

        self.stdout.write(self.style.SUCCESS('\n🎉 SOOD-74 completado!'))
