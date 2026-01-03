from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente
from pacientes.models import Paciente
from clinicas.models import Clinica


class CategoriaEnfermedadModelTest(TestCase):
    """Tests para modelo CategoriaEnfermedad (SOOD-71)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com"
        )
    
    def test_crear_categoria_enfermedad(self):
        """Test creación básica de categoría"""
        categoria = CategoriaEnfermedad.objects.create(
            nombre="Cardiovascular",
            descripcion="Enfermedades del sistema cardiovascular",
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(categoria.nombre, "Cardiovascular")
        self.assertTrue(categoria.estado)
        self.assertEqual(str(categoria), "Cardiovascular")
    
    def test_categoria_nombre_unico(self):
        """Test que nombre de categoría sea único"""
        CategoriaEnfermedad.objects.create(
            nombre="Diabetes",
            uc=self.user,
            um=self.user.id
        )
        with self.assertRaises(Exception):
            CategoriaEnfermedad.objects.create(
                nombre="Diabetes",
                uc=self.user,
                um=self.user.id
            )
    
    def test_categoria_nombre_requerido(self):
        """Test que nombre sea obligatorio"""
        categoria = CategoriaEnfermedad(
            descripcion="Test",
            uc=self.user,
            um=self.user.id
        )
        with self.assertRaises(ValidationError):
            categoria.full_clean()


class EnfermedadModelTest(TestCase):
    """Tests para modelo Enfermedad (SOOD-72)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com"
        )
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre="Cardiovascular",
            descripcion="Test",
            uc=self.user,
            um=self.user.id
        )
    
    def test_crear_enfermedad_completa(self):
        """Test creación de enfermedad con todos los campos"""
        enfermedad = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hipertensión Arterial",
            nombre_cientifico="Hipertensión Esencial",
            codigo_cie10="I10",
            descripcion="Presión arterial elevada crónica",
            nivel_riesgo="ALTO",
            contraindicaciones="Evitar vasoconstrictores en exceso",
            precauciones="Monitorear presión arterial antes de procedimientos",
            requiere_interconsulta=True,
            genera_alerta_roja=False,
            genera_alerta_amarilla=True,
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(enfermedad.nombre, "Hipertensión Arterial")
        self.assertEqual(enfermedad.nivel_riesgo, "ALTO")
        self.assertTrue(enfermedad.requiere_interconsulta)
        self.assertTrue(enfermedad.genera_alerta_amarilla)
        self.assertFalse(enfermedad.genera_alerta_roja)
    
    def test_enfermedad_str_con_codigo(self):
        """Test representación string con código CIE-10"""
        enfermedad = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Diabetes",
            codigo_cie10="E11",
            nivel_riesgo="ALTO",
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(str(enfermedad), "Diabetes (E11)")
    
    def test_enfermedad_str_sin_codigo(self):
        """Test representación string sin código CIE-10"""
        enfermedad = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Otra Condición",
            nivel_riesgo="BAJO",
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(str(enfermedad), "Otra Condición")
    
    def test_niveles_riesgo_validos(self):
        """Test que niveles de riesgo sean válidos"""
        niveles = ["BAJO", "MEDIO", "ALTO", "CRITICO"]
        for nivel in niveles:
            enfermedad = Enfermedad(
                categoria=self.categoria,
                nombre=f"Test {nivel}",
                nivel_riesgo=nivel,
                uc=self.user,
                um=self.user.id
            )
            enfermedad.full_clean()  # No debe lanzar error
            self.assertEqual(enfermedad.nivel_riesgo, nivel)
    
    def test_enfermedad_critica_genera_alerta_roja(self):
        """Test que enfermedades críticas pueden generar alerta roja"""
        enfermedad = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hemofilia",
            codigo_cie10="D66",
            nivel_riesgo="CRITICO",
            genera_alerta_roja=True,
            requiere_interconsulta=True,
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(enfermedad.nivel_riesgo, "CRITICO")
        self.assertTrue(enfermedad.genera_alerta_roja)
        self.assertTrue(enfermedad.requiere_interconsulta)
    
    def test_codigo_cie10_unico(self):
        """Test que código CIE-10 sea único cuando se proporciona"""
        Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Enfermedad 1",
            codigo_cie10="I21",
            nivel_riesgo="CRITICO",
            uc=self.user,
            um=self.user.id
        )
        with self.assertRaises(Exception):
            Enfermedad.objects.create(
                categoria=self.categoria,
                nombre="Enfermedad 2",
                codigo_cie10="I21",  # Mismo código
                nivel_riesgo="CRITICO",
                uc=self.user,
                um=self.user.id
            )
    
    def test_enfermedad_categoria_requerida(self):
        """Test que categoría sea obligatoria"""
        enfermedad = Enfermedad(
            nombre="Test",
            nivel_riesgo="BAJO",
            uc=self.user,
            um=self.user.id
        )
        with self.assertRaises(ValidationError):
            enfermedad.full_clean()


class EnfermedadPacienteModelTest(TestCase):
    """Tests para modelo EnfermedadPaciente - M2M through (SOOD-73)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com"
        )
        self.clinica = Clinica.objects.create(
            nombre="Clinica Test",
            ruc="1234567890001",
            direccion="Dir test",
            telefono="0999999999",
            email="clinic@test.com",
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre="Cardiovascular",
            uc=self.user,
            um=self.user.id
        )
        self.paciente = Paciente.objects.create(
            nombres="Juan",
            apellidos="Perez",
            cedula="1234567890",
            fecha_nacimiento=date(1990, 1, 1),
            genero="M",
            telefono="0999999999",
            email="juan@test.com",
            uc=self.user,
            um=self.user.id
        )
        self.enfermedad = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Diabetes",
            codigo_cie10="E11",
            nivel_riesgo="ALTO",
            uc=self.user,
            um=self.user.id
        )
    
    def test_crear_relacion_enfermedad_paciente(self):
        """Test creación de relación M2M entre enfermedad y paciente"""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            fecha_diagnostico=date(2025, 6, 15),
            observaciones="Diabetes tipo 2 controlada con metformina",
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(relacion.paciente, self.paciente)
        self.assertEqual(relacion.enfermedad, self.enfermedad)
        self.assertEqual(relacion.observaciones, "Diabetes tipo 2 controlada con metformina")
        self.assertTrue(relacion.estado)
    
    def test_str_relacion_enfermedad_paciente(self):
        """Test representación string de la relación"""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        # El formato real es: "Apellidos, Nombres - Cédula - Enfermedad (CIE) (Estado)"
        expected = "Perez, Juan - 1234567890 - Diabetes (E11) (ACTIVA)"
        self.assertEqual(str(relacion), expected)
    
    def test_paciente_puede_tener_multiples_enfermedades(self):
        """Test que un paciente puede tener múltiples enfermedades"""
        enfermedad2 = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hipertensión",
            codigo_cie10="I10",
            nivel_riesgo="ALTO",
            uc=self.user,
            um=self.user.id
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enfermedad2,
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(self.paciente.enfermedades.count(), 2)
        self.assertIn(self.enfermedad, self.paciente.enfermedades.all())
        self.assertIn(enfermedad2, self.paciente.enfermedades.all())
    
    def test_enfermedad_puede_asociarse_multiples_pacientes(self):
        """Test que una enfermedad puede estar en múltiples pacientes"""
        paciente2 = Paciente.objects.create(
            nombres="Maria",
            apellidos="Lopez",
            cedula="0987654321",
            fecha_nacimiento=date(1985, 5, 20),
            genero="F",
            telefono="0988888888",
            email="maria@test.com",
            uc=self.user,
            um=self.user.id
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=paciente2,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(self.enfermedad.pacientes.count(), 2)
    
    def test_relacion_unica_paciente_enfermedad(self):
        """Test que no se pueda crear la misma relación dos veces"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        with self.assertRaises(Exception):
            EnfermedadPaciente.objects.create(
                paciente=self.paciente,
                enfermedad=self.enfermedad,  # Misma combinación
                uc=self.user,
                um=self.user.id
            )
    
    def test_fecha_diagnostico_opcional(self):
        """Test que fecha de diagnóstico sea opcional"""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            fecha_diagnostico=None,
            uc=self.user,
            um=self.user.id
        )
        self.assertIsNone(relacion.fecha_diagnostico)
    
    def test_observaciones_opcional(self):
        """Test que observaciones sea opcional"""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            uc=self.user,
            um=self.user.id
        )
        # observaciones tiene default=None en el modelo
        self.assertIsNone(relacion.observaciones)
    
    def test_relacion_inactiva(self):
        """Test que se pueda marcar relación como inactiva (enfermedad curada/controlada)"""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            estado=False,  # Ya no tiene esta enfermedad
            observaciones="Curada en 2024",
            uc=self.user,
            um=self.user.id
        )
        self.assertFalse(relacion.estado)
        
        # Verificar que no se cuenta en enfermedades activas
        enfermedades_activas = self.paciente.enfermedades.filter(
            pacientes_afectados__estado=True
        )
        self.assertEqual(enfermedades_activas.count(), 0)


class IntegracionPacienteEnfermedadesTest(TestCase):
    """Tests de integración entre Paciente y Enfermedades (SOOD-75)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="testpass123"
        )
        self.clinica = Clinica.objects.create(
            nombre="Clinica Test",
            ruc="1234567890001",
            direccion="Dir",
            telefono="0999999999",
            email="clinic@test.com",
            uc=self.user,
            um=self.user.id
        )
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre="Test",
            uc=self.user,
            um=self.user.id
        )
        self.paciente = Paciente.objects.create(
            nombres="Test",
            apellidos="User",
            cedula="1234567890",
            fecha_nacimiento=date(1990, 1, 1),
            genero="M",
            telefono="0999999999",
            email="test@test.com",
            uc=self.user,
            um=self.user.id
        )
    
    def test_get_enfermedades_criticas(self):
        """Test método get_enfermedades_criticas del paciente"""
        enf_critica = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hemofilia",
            nivel_riesgo="CRITICO",
            genera_alerta_roja=True,
            uc=self.user,
            um=self.user.id
        )
        enf_normal = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hipertensión",
            nivel_riesgo="ALTO",
            uc=self.user,
            um=self.user.id
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enf_critica,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enf_normal,
            uc=self.user,
            um=self.user.id
        )
        
        criticas = self.paciente.get_enfermedades_criticas()
        self.assertEqual(criticas.count(), 1)
        self.assertIn(enf_critica, criticas)
        self.assertNotIn(enf_normal, criticas)
    
    def test_tiene_enfermedades_criticas(self):
        """Test método tiene_enfermedades_criticas"""
        self.assertFalse(self.paciente.tiene_enfermedades_criticas())
        
        enf = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="IAM",
            nivel_riesgo="CRITICO",
            genera_alerta_roja=True,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enf,
            uc=self.user,
            um=self.user.id
        )
        
        self.assertTrue(self.paciente.tiene_enfermedades_criticas())
    
    def test_calcular_nivel_alerta_integrado(self):
        """Test cálculo de alerta con enfermedades reales"""
        # Sin enfermedades
        self.assertEqual(self.paciente.calcular_nivel_alerta(), 'VERDE')
        
        # Con enfermedad ALTA
        enf_alta = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Diabetes",
            nivel_riesgo="ALTO",
            genera_alerta_amarilla=True,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enf_alta,
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(self.paciente.calcular_nivel_alerta(), 'AMARILLO')
        
        # Agregar enfermedad CRITICA
        enf_critica = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hemofilia",
            nivel_riesgo="CRITICO",
            genera_alerta_roja=True,
            uc=self.user,
            um=self.user.id
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enf_critica,
            uc=self.user,
            um=self.user.id
        )
        self.assertEqual(self.paciente.calcular_nivel_alerta(), 'ROJO')
