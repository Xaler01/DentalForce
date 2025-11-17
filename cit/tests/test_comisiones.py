"""
Tests para el modelo ComisionDentista y funcionalidad de comisiones.
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from cit.models import ComisionDentista, Dentista, Especialidad, Clinica, Sucursal


class ComisionDentistaModelTest(TestCase):
    """Tests para el modelo ComisionDentista"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario para tests
        self.user = User.objects.create_user(username='testuser', password='test123')
        
        # Crear clínica y sucursal
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='0987654321',
            email='test@test.com',
            uc=self.user
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Principal',
            direccion='Av. Test 123',
            telefono='0987654321',
            horario_apertura='08:00',
            horario_cierre='18:00',
            uc=self.user
        )
        
        # Crear especialidad
        self.especialidad = Especialidad.objects.create(
            nombre='Endodoncia',
            descripcion='Endodoncia',
            duracion_default=60,
            color_calendario='#3498db',
            uc=self.user
        )
        
        # Crear dentista
        user_dentista = User.objects.create_user(
            username='dentista',
            password='test123',
            first_name='Juan Carlos',
            last_name='Pérez López',
            email='juan.perez@test.com'
        )
        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            cedula_profesional='1234567890',
            numero_licencia='LIC-12345',
            telefono_movil='0987654321',
            fecha_contratacion='2024-01-01',
            sucursal_principal=self.sucursal,
            uc=self.user
        )
        self.dentista.especialidades.add(self.especialidad)
    
    def test_crear_comision_porcentaje(self):
        """Test para crear una comisión de tipo porcentaje"""
        comision = ComisionDentista.objects.create(
            dentista=self.dentista,
            especialidad=self.especialidad,
            tipo_comision='PORCENTAJE',
            porcentaje=Decimal('15.50'),
            activo=True,
            uc=self.user
        )
        
        self.assertEqual(comision.dentista, self.dentista)
        self.assertEqual(comision.especialidad, self.especialidad)
        self.assertEqual(comision.tipo_comision, 'PORCENTAJE')
        self.assertEqual(comision.porcentaje, Decimal('15.50'))
        self.assertTrue(comision.activo)
        self.assertIsNone(comision.valor_fijo)
    
    def test_crear_comision_valor_fijo(self):
        """Test para crear una comisión de valor fijo"""
        comision = ComisionDentista.objects.create(
            dentista=self.dentista,
            especialidad=self.especialidad,
            tipo_comision='FIJO',
            valor_fijo=Decimal('50.00'),
            activo=True,
            uc=self.user
        )
        
        self.assertEqual(comision.tipo_comision, 'FIJO')
        self.assertEqual(comision.valor_fijo, Decimal('50.00'))
        self.assertIsNone(comision.porcentaje)
    
    def test_comision_activa_por_defecto(self):
        """Test para verificar que las comisiones se crean activas por defecto"""
        comision = ComisionDentista.objects.create(
            dentista=self.dentista,
            especialidad=self.especialidad,
            tipo_comision='PORCENTAJE',
            porcentaje=Decimal('10.00'),
            uc=self.user
        )
        
        self.assertTrue(comision.activo)
    
    def test_multiple_comisiones_mismo_dentista(self):
        """Test para verificar que un dentista puede tener múltiples comisiones"""
        # Crear otra especialidad
        otra_especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Ortodoncia',
            duracion_default=60,
            color_calendario='#e74c3c',
            uc=self.user
        )
        self.dentista.especialidades.add(otra_especialidad)
        
        # Crear dos comisiones
        comision1 = ComisionDentista.objects.create(
            dentista=self.dentista,
            especialidad=self.especialidad,
            tipo_comision='PORCENTAJE',
            porcentaje=Decimal('15.00'),
            uc=self.user
        )
        
        comision2 = ComisionDentista.objects.create(
            dentista=self.dentista,
            especialidad=otra_especialidad,
            tipo_comision='FIJO',
            valor_fijo=Decimal('30.00'),
            uc=self.user
        )
        
        comisiones = self.dentista.comisiones.all()
        self.assertEqual(comisiones.count(), 2)
        self.assertIn(comision1, comisiones)
        self.assertIn(comision2, comisiones)
