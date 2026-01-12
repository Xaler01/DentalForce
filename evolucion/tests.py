"""
Tests simples para el módulo de evolución.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date

from pacientes.models import Paciente
from clinicas.models import Clinica
from procedimientos.models import ProcedimientoOdontologico
from personal.models import Dentista

from .models import (
    Odontograma,
    PiezaDental,
    HistoriaClinicaOdontologica,
    PlanTratamiento,
    ProcedimientoEnPlan,
    EvolucionConsulta,
    ProcedimientoEnEvolucion,
)


class OdontogramaTestCase(TestCase):
    """Tests para Odontograma"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='1234567890',
            direccion='Calle Test 123',
            uc_id=cls.user.id
        )
        cls.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='123456789',
            telefono='9876543210',
            email='juan@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
    
    def test_crear_odontograma(self):
        """Test creación de odontograma"""
        odonto = Odontograma.objects.create(
            paciente=self.paciente,
            tipo_denticion='ADULTO',
            uc=self.user
        )
        self.assertEqual(odonto.paciente, self.paciente)
        self.assertEqual(odonto.tipo_denticion, 'ADULTO')
        self.assertTrue(str(odonto).startswith('Odontograma de'))
    
    def test_get_piezas_afectadas(self):
        """Test método get_piezas_afectadas"""
        odonto = Odontograma.objects.create(
            paciente=self.paciente,
            tipo_denticion='ADULTO',
            uc=self.user
        )
        self.assertEqual(odonto.get_piezas_afectadas(), 0)
        
        PiezaDental.objects.create(
            odontograma=odonto,
            numero=11,
            nombre_anatomico='Incisivo',
            estado='CARIES',
            uc=self.user
        )
        self.assertEqual(odonto.get_piezas_afectadas(), 1)


class PiezaDentalTestCase(TestCase):
    """Tests para PiezaDental"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='1234567890',
            direccion='Calle Test 123',
            uc_id=cls.user.id
        )
        cls.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='123456789',
            telefono='9876543210',
            email='juan@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
        cls.odonto = Odontograma.objects.create(
            paciente=cls.paciente,
            tipo_denticion='ADULTO',
            uc=cls.user
        )
    
    def test_crear_pieza(self):
        """Test creación de pieza dental"""
        pieza = PiezaDental.objects.create(
            odontograma=self.odonto,
            numero=11,
            nombre_anatomico='Incisivo Central',
            estado='SANA',
            uc=self.user
        )
        self.assertEqual(pieza.numero, 11)
        self.assertEqual(pieza.estado, 'SANA')
    
    def test_pieza_unique_constraint(self):
        """Test restricción única en número de pieza"""
        PiezaDental.objects.create(
            odontograma=self.odonto,
            numero=11,
            nombre_anatomico='Incisivo',
            estado='SANA',
            uc=self.user
        )
        
        with self.assertRaises(Exception):
            PiezaDental.objects.create(
                odontograma=self.odonto,
                numero=11,
                nombre_anatomico='Incisivo',
                estado='CARIES',
                uc=self.user
            )


class HistoriaClinicaTestCase(TestCase):
    """Tests para HistoriaClinicaOdontologica"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='1234567890',
            direccion='Calle Test 123',
            uc_id=cls.user.id
        )
        cls.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='123456789',
            telefono='9876543210',
            email='juan@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
    
    def test_crear_historia(self):
        """Test creación de historia clínica"""
        historia = HistoriaClinicaOdontologica.objects.create(
            paciente=self.paciente,
            antecedentes_medicos='Hipertensión',
            alergias='Penicilina',
            uc=self.user
        )
        self.assertEqual(historia.paciente, self.paciente)
        self.assertEqual(historia.alergias, 'Penicilina')


class PlanTratamientoTestCase(TestCase):
    """Tests para PlanTratamiento"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='1234567890',
            direccion='Calle Test 123',
            uc_id=cls.user.id
        )
        cls.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='123456789',
            telefono='9876543210',
            email='juan@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
        cls.proc1 = ProcedimientoOdontologico.objects.create(
            codigo='TEST-001',
            nombre='Limpieza',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            uc=cls.user
        )
        cls.proc2 = ProcedimientoOdontologico.objects.create(
            codigo='TEST-002',
            nombre='Extracción',
            categoria='CIRUGÍA',
            duracion_estimada=45,
            uc=cls.user
        )
    
    def test_crear_plan(self):
        """Test creación de plan"""
        plan = PlanTratamiento.objects.create(
            paciente=self.paciente,
            nombre='Plan integral',
            presupuesto_estimado=1500.00,
            uc=self.user
        )
        self.assertEqual(plan.paciente, self.paciente)
        self.assertEqual(plan.estado, 'PENDIENTE')
    
    def test_progreso_sin_procedimientos(self):
        """Test progreso sin procedimientos"""
        plan = PlanTratamiento.objects.create(
            paciente=self.paciente,
            nombre='Plan test',
            presupuesto_estimado=1500.00,
            uc=self.user
        )
        self.assertEqual(plan.get_progreso(), 0)
    
    def test_progreso_con_procedimientos(self):
        """Test progreso con procedimientos"""
        plan = PlanTratamiento.objects.create(
            paciente=self.paciente,
            nombre='Plan test',
            presupuesto_estimado=1500.00,
            uc=self.user
        )
        
        ProcedimientoEnPlan.objects.create(
            plan=plan,
            procedimiento=self.proc1,
            orden=1,
            precio=500.00,
            realizado=True,
            uc=self.user
        )
        ProcedimientoEnPlan.objects.create(
            plan=plan,
            procedimiento=self.proc2,
            orden=2,
            precio=500.00,
            realizado=False,
            uc=self.user
        )
        
        self.assertEqual(plan.get_progreso(), 50)


class EvolucionConsultaTestCase(TestCase):
    """Tests para EvolucionConsulta"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='1234567890',
            direccion='Calle Test 123',
            uc_id=cls.user.id
        )
        cls.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='123456789',
            telefono='9876543210',
            email='juan@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
        cls.proc = ProcedimientoOdontologico.objects.create(
            codigo='TEST-001',
            nombre='Extracción',
            categoria='CIRUGÍA',
            duracion_estimada=45,
            uc=cls.user
        )
    
    def test_crear_evolucion(self):
        """Test creación de evolución"""
        evolucion = EvolucionConsulta.objects.create(
            paciente=self.paciente,
            fecha_consulta=date.today(),
            motivo_consulta='Dolor molar',
            uc=self.user
        )
        self.assertEqual(evolucion.paciente, self.paciente)
        self.assertEqual(evolucion.motivo_consulta, 'Dolor molar')
    
    def test_evolucion_con_procedimientos(self):
        """Test evolución con procedimientos"""
        evolucion = EvolucionConsulta.objects.create(
            paciente=self.paciente,
            fecha_consulta=date.today(),
            motivo_consulta='Dolor',
            uc=self.user
        )
        
        ProcedimientoEnEvolucion.objects.create(
            evolucion=evolucion,
            procedimiento=self.proc,
            cantidad=1,
            uc=self.user
        )
        
        self.assertEqual(evolucion.procedimientos.count(), 1)
