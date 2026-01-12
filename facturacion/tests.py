from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from clinicas.models import Clinica
from pacientes.models import Paciente
from procedimientos.models import ProcedimientoOdontologico
from .models import Factura, ItemFactura, Pago
from . import services


class FacturaBasicTest(TestCase):
    """Test basico de facturacion"""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
        cls.clinica = Clinica.objects.create(
            nombre='Test Clinic',
            email='test@example.com',
            uc=cls.user
        )
        cls.paciente = Paciente.objects.create(
            nombres='Test',
            apellidos='Patient',
            cedula='1234567890',
            email='patient@example.com',
            clinica=cls.clinica,
            uc=cls.user
        )
        cls.proc = ProcedimientoOdontologico.objects.create(
            codigo='TST-001',
            nombre='Test Procedure',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            uc=cls.user
        )
    
    def test_crear_factura(self):
        f = Factura.objects.create(
            paciente=self.paciente,
            clinica=self.clinica,
            uc=self.user
        )
        self.assertIsNotNone(f.numero_factura)
        self.assertTrue(f.numero_factura.startswith('FX-'))
    
    def test_multitenant_segregation(self):
        user2 = User.objects.create_user(username='user2', password='pass')
        clinica2 = Clinica.objects.create(
            nombre='Clinica 2',
            email='clinic2@example.com',
            uc=user2
        )
        pac2 = Paciente.objects.create(
            nombres='Patient',
            apellidos='Two',
            cedula='9876543210',
            email='patient2@example.com',
            clinica=clinica2,
            uc=user2
        )
        
        f1 = Factura.objects.create(
            paciente=self.paciente,
            clinica=self.clinica,
            uc=self.user
        )
        f2 = Factura.objects.create(
            paciente=pac2,
            clinica=clinica2,
            uc=user2
        )
        
        facturas = services.facturas_para_clinica(self.clinica.id)
        self.assertEqual(facturas.count(), 1)
        self.assertIn(f1, facturas)
        self.assertNotIn(f2, facturas)
