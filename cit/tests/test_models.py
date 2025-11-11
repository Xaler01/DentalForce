from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cit.models import Clinica, Sucursal, Especialidad, Cubiculo
from datetime import time


class ClinicaModelTest(TestCase):
    """Tests para el modelo Clinica"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_clinica(self):
        """Test: Crear una clínica con todos los campos"""
        clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(clinica.nombre, 'Clínica Test')
        self.assertEqual(clinica.telefono, '02-1234567')
        self.assertTrue(clinica.estado)
        self.assertIsNotNone(clinica.fc)
    
    def test_clinica_str_representation(self):
        """Test: Representación en string de la clínica"""
        clinica = Clinica.objects.create(
            nombre='PowerDent',
            direccion='Av Principal',
            telefono='02-9999999',
            email='info@powerdent.com',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(str(clinica), 'PowerDent')
    
    def test_clinica_telefono_invalido(self):
        """Test: Validación de teléfono inválido"""
        clinica = Clinica(
            nombre='Clínica Test',
            direccion='Calle Test',
            telefono='123',  # Teléfono muy corto
            email='test@test.com',
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            clinica.full_clean()
    
    def test_clinica_nombre_unico(self):
        """Test: El nombre de la clínica debe ser único"""
        Clinica.objects.create(
            nombre='Clínica Única',
            direccion='Calle 1',
            telefono='02-1111111',
            email='unica@test.com',
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar crear otra con el mismo nombre
        clinica2 = Clinica(
            nombre='Clínica Única',
            direccion='Calle 2',
            telefono='02-2222222',
            email='otra@test.com',
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            clinica2.full_clean()


class SucursalModelTest(TestCase):
    """Tests para el modelo Sucursal"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.clinica = Clinica.objects.create(
            nombre='Clínica Principal',
            direccion='Av Central',
            telefono='02-3333333',
            email='principal@test.com',
            uc=self.user,
            um=self.user.id
        )
    
    def test_crear_sucursal(self):
        """Test: Crear una sucursal con FK a clínica"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Norte',
            direccion='Av Norte 123',
            telefono='02-4444444',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(sucursal.clinica, self.clinica)
        self.assertEqual(sucursal.nombre, 'Sucursal Norte')
        self.assertTrue(sucursal.estado)
    
    def test_sucursal_str_representation(self):
        """Test: Representación en string de sucursal"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sur',
            direccion='Av Sur',
            telefono='02-5555555',
            horario_apertura=time(9, 0),
            horario_cierre=time(19, 0),
            uc=self.user,
            um=self.user.id
        )
        
        expected = f"{self.clinica.nombre} - Sur"
        self.assertEqual(str(sucursal), expected)
    
    def test_sucursal_horario_invalido(self):
        """Test: Validación - cierre debe ser después de apertura"""
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Av Test',
            telefono='02-6666666',
            horario_apertura=time(18, 0),
            horario_cierre=time(9, 0),  # Cierre antes de apertura
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            sucursal.full_clean()
    
    def test_sucursal_cascade_delete(self):
        """Test: Al eliminar clínica, se eliminan sus sucursales (CASCADE)"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Temporal',
            direccion='Av Temporal',
            telefono='02-7777777',
            horario_apertura=time(8, 0),
            horario_cierre=time(17, 0),
            uc=self.user,
            um=self.user.id
        )
        
        sucursal_id = sucursal.id
        self.clinica.delete()
        
        # Verificar que la sucursal también se eliminó
        self.assertFalse(Sucursal.objects.filter(id=sucursal_id).exists())
    
    def test_sucursal_unique_together(self):
        """Test: No puede haber sucursales con el mismo nombre en la misma clínica"""
        Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Única',
            direccion='Calle 1',
            telefono='02-8888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar crear otra con el mismo nombre en la misma clínica
        sucursal2 = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Única',
            direccion='Calle 2',
            telefono='02-9999999',
            horario_apertura=time(9, 0),
            horario_cierre=time(19, 0),
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            sucursal2.full_clean()
    
    def test_sucursal_dias_atencion_default(self):
        """Test: El campo días_atencion tiene valor por defecto"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Default',
            direccion='Av Default',
            telefono='02-1010101',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(sucursal.dias_atencion, 'Lunes a Viernes')


class EspecialidadModelTest(TestCase):
    """Tests para el modelo Especialidad"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_especialidad(self):
        """Test: Crear una especialidad con todos los campos"""
        especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Especialidad enfocada en la corrección de dientes',
            duracion_default=45,
            color_calendario='#3498db',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(especialidad.nombre, 'Ortodoncia')
        self.assertEqual(especialidad.duracion_default, 45)
        self.assertEqual(especialidad.color_calendario, '#3498db')
        self.assertTrue(especialidad.estado)
    
    def test_especialidad_str_representation(self):
        """Test: Representación en string de especialidad"""
        especialidad = Especialidad.objects.create(
            nombre='Endodoncia',
            duracion_default=60,
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(str(especialidad), 'Endodoncia')
    
    def test_especialidad_duracion_invalida(self):
        """Test: Validación de duración mínima (15 minutos)"""
        especialidad = Especialidad(
            nombre='Test',
            duracion_default=10,  # Menor a 15 minutos
            color_calendario='#ff0000',
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            especialidad.full_clean()
    
    def test_especialidad_color_invalido(self):
        """Test: Validación de formato hexadecimal de color"""
        especialidad = Especialidad(
            nombre='Test Color',
            duracion_default=30,
            color_calendario='azul',  # No es formato hexadecimal
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            especialidad.full_clean()
    
    def test_especialidad_nombre_unico(self):
        """Test: El nombre de la especialidad debe ser único"""
        Especialidad.objects.create(
            nombre='Periodoncia',
            duracion_default=40,
            uc=self.user,
            um=self.user.id
        )
        
        especialidad2 = Especialidad(
            nombre='Periodoncia',  # Nombre duplicado
            duracion_default=30,
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            especialidad2.full_clean()
    
    def test_especialidad_duracion_default(self):
        """Test: Valor por defecto de duración es 30 minutos"""
        especialidad = Especialidad.objects.create(
            nombre='Limpieza',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(especialidad.duracion_default, 30)


class CubiculoModelTest(TestCase):
    """Tests para el modelo Cubiculo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av Test',
            telefono='02-1111111',
            email='test@test.com',
            uc=self.user,
            um=self.user.id
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Principal',
            direccion='Av Principal',
            telefono='02-2222222',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.user,
            um=self.user.id
        )
    
    def test_crear_cubiculo(self):
        """Test: Crear un cubículo con FK a sucursal"""
        cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            numero=1,
            capacidad=3,
            equipamiento='Silla dental, lámpara, rayos X',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(cubiculo.sucursal, self.sucursal)
        self.assertEqual(cubiculo.numero, 1)
        self.assertEqual(cubiculo.capacidad, 3)
        self.assertTrue(cubiculo.estado)
    
    def test_cubiculo_str_representation(self):
        """Test: Representación en string de cubículo"""
        cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Sala de Cirugía',
            numero=5,
            uc=self.user,
            um=self.user.id
        )
        
        # El nombre se guarda sin normalizar porque clean() se llama solo con full_clean()
        expected = f"{self.sucursal.nombre} - Sala de Cirugía (#{cubiculo.numero})"
        self.assertEqual(str(cubiculo), expected)
    
    def test_cubiculo_capacidad_default(self):
        """Test: Valor por defecto de capacidad es 2"""
        cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio Default',
            numero=10,
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(cubiculo.capacidad, 2)
    
    def test_cubiculo_capacidad_invalida(self):
        """Test: Validación de capacidad mínima (1 persona)"""
        cubiculo = Cubiculo(
            sucursal=self.sucursal,
            nombre='Test',
            numero=1,
            capacidad=0,  # Capacidad inválida
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            cubiculo.full_clean()
    
    def test_cubiculo_numero_invalido(self):
        """Test: Validación de número positivo"""
        cubiculo = Cubiculo(
            sucursal=self.sucursal,
            nombre='Test',
            numero=0,  # Número inválido
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            cubiculo.full_clean()
    
    def test_cubiculo_cascade_delete(self):
        """Test: Al eliminar sucursal, se eliminan sus cubículos (CASCADE)"""
        cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Temporal',
            numero=99,
            uc=self.user,
            um=self.user.id
        )
        
        cubiculo_id = cubiculo.id
        self.sucursal.delete()
        
        # Verificar que el cubículo también se eliminó
        self.assertFalse(Cubiculo.objects.filter(id=cubiculo_id).exists())
    
    def test_cubiculo_unique_together(self):
        """Test: No puede haber cubículos con el mismo número en la misma sucursal"""
        Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio A',
            numero=7,
            uc=self.user,
            um=self.user.id
        )
        
        cubiculo2 = Cubiculo(
            sucursal=self.sucursal,
            nombre='Consultorio B',
            numero=7,  # Mismo número en la misma sucursal
            uc=self.user,
            um=self.user.id
        )
        
        with self.assertRaises(ValidationError):
            cubiculo2.full_clean()
