from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cit.models import Clinica, Sucursal, Especialidad, Cubiculo, Dentista, Paciente
from datetime import time, date


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


class DentistaModelTest(TestCase):
    """Tests para el modelo Dentista"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        
        # Crear usuarios para dentistas
        self.user1 = User.objects.create_user(
            username='dr_martinez',
            password='pass123',
            first_name='Juan',
            last_name='Martínez'
        )
        
        self.user2 = User.objects.create_user(
            username='dra_garcia',
            password='pass123',
            first_name='María',
            last_name='García'
        )
        
        # Crear clínica y sucursal
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av Test',
            telefono='02-1111111',
            email='test@test.com',
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Principal',
            direccion='Av Principal',
            telefono='02-2222222',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        # Crear especialidades
        self.ortodoncia = Especialidad.objects.create(
            nombre='Ortodoncia',
            duracion_default=45,
            color_calendario='#3498db',
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.endodoncia = Especialidad.objects.create(
            nombre='Endodoncia',
            duracion_default=60,
            color_calendario='#e74c3c',
            uc=self.admin_user,
            um=self.admin_user.id
        )
    
    def test_crear_dentista(self):
        """Test: Crear un dentista con todos los campos"""
        dentista = Dentista.objects.create(
            usuario=self.user1,
            sucursal_principal=self.sucursal,
            cedula_profesional='1234567',
            numero_licencia='LIC-2025-001',
            telefono_movil='0999-123456',
            fecha_contratacion=date(2025, 1, 15),
            biografia='Especialista en ortodoncia',
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        dentista.especialidades.add(self.ortodoncia)
        
        self.assertEqual(dentista.usuario, self.user1)
        self.assertEqual(dentista.cedula_profesional, '1234567')
        self.assertEqual(dentista.especialidades.count(), 1)
        self.assertTrue(dentista.estado)
    
    def test_dentista_str_representation(self):
        """Test: Representación en string de dentista"""
        dentista = Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='9876543',
            numero_licencia='LIC-2025-002',
            telefono_movil='0999-654321',
            fecha_contratacion=date(2025, 2, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        expected = "Dr(a). Juan Martínez"
        self.assertEqual(str(dentista), expected)
    
    def test_dentista_multiples_especialidades(self):
        """Test: Un dentista puede tener múltiples especialidades (M2M)"""
        dentista = Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='5555555',
            numero_licencia='LIC-2025-003',
            telefono_movil='0999-555555',
            fecha_contratacion=date(2025, 3, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        dentista.especialidades.add(self.ortodoncia, self.endodoncia)
        
        self.assertEqual(dentista.especialidades.count(), 2)
        self.assertIn(self.ortodoncia, dentista.especialidades.all())
        self.assertIn(self.endodoncia, dentista.especialidades.all())
    
    def test_dentista_cedula_unica(self):
        """Test: La cédula profesional debe ser única"""
        Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='CEDULA-123',
            numero_licencia='LIC-2025-004',
            telefono_movil='0999-111111',
            fecha_contratacion=date(2025, 4, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        # Intentar crear otro dentista con la misma cédula
        dentista2 = Dentista(
            usuario=self.user2,
            cedula_profesional='CEDULA-123',  # Cédula duplicada
            numero_licencia='LIC-2025-005',
            telefono_movil='0999-222222',
            fecha_contratacion=date(2025, 5, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError):
            dentista2.full_clean()
    
    def test_dentista_licencia_unica(self):
        """Test: El número de licencia debe ser único"""
        Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='CED-001',
            numero_licencia='LICENCIA-UNICA',
            telefono_movil='0999-333333',
            fecha_contratacion=date(2025, 6, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        dentista2 = Dentista(
            usuario=self.user2,
            cedula_profesional='CED-002',
            numero_licencia='LICENCIA-UNICA',  # Licencia duplicada
            telefono_movil='0999-444444',
            fecha_contratacion=date(2025, 7, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError):
            dentista2.full_clean()
    
    def test_dentista_cedula_formato_invalido(self):
        """Test: Validación de formato de cédula profesional"""
        dentista = Dentista(
            usuario=self.user1,
            cedula_profesional='ABC-XYZ',  # Formato inválido (solo letras)
            numero_licencia='LIC-2025-006',
            telefono_movil='0999-555555',
            fecha_contratacion=date(2025, 8, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError):
            dentista.full_clean()
    
    def test_dentista_telefono_invalido(self):
        """Test: Validación de teléfono móvil"""
        dentista = Dentista(
            usuario=self.user1,
            cedula_profesional='123456',
            numero_licencia='LIC-2025-007',
            telefono_movil='123',  # Teléfono muy corto
            fecha_contratacion=date(2025, 9, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError):
            dentista.full_clean()
    
    def test_dentista_fecha_contratacion_futura(self):
        """Test: La fecha de contratación no puede ser futura"""
        fecha_futura = date(2026, 12, 31)
        
        dentista = Dentista(
            usuario=self.user1,
            cedula_profesional='654321',
            numero_licencia='LIC-2025-008',
            telefono_movil='0999-666666',
            fecha_contratacion=fecha_futura,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError):
            dentista.full_clean()
    
    def test_dentista_onetoone_usuario(self):
        """Test: Relación OneToOne - un usuario solo puede tener un dentista"""
        # Crear primer dentista
        Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='111111',
            numero_licencia='LIC-2025-009',
            telefono_movil='0999-777777',
            fecha_contratacion=date(2025, 10, 1),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        # Intentar crear otro dentista con el mismo usuario
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Dentista.objects.create(
                usuario=self.user1,  # Usuario ya usado
                cedula_profesional='222222',
                numero_licencia='LIC-2025-010',
                telefono_movil='0999-888888',
                fecha_contratacion=date(2025, 11, 1),
                uc=self.admin_user,
                um=self.admin_user.id
            )
    
    def test_get_especialidades_nombres(self):
        """Test: Método para obtener nombres de especialidades"""
        dentista = Dentista.objects.create(
            usuario=self.user1,
            cedula_profesional='333333',
            numero_licencia='LIC-2025-011',
            telefono_movil='0999-999999',
            fecha_contratacion=date(2025, 11, 15),
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        dentista.especialidades.add(self.ortodoncia, self.endodoncia)
        
        nombres = dentista.get_especialidades_nombres()
        self.assertIn('Ortodoncia', nombres)
        self.assertIn('Endodoncia', nombres)


class PacienteModelTest(TestCase):
    """Tests para el modelo Paciente"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Usuario admin para auditoría
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        # Crear clínica
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            telefono='098-123456',
            direccion='Av. Test 123',
            email='test@clinica.com',
            uc=self.admin_user,
            um=self.admin_user.id
        )
    
    def test_crear_paciente(self):
        """Test: Crear paciente correctamente"""
        paciente = Paciente.objects.create(
            nombres='Juan Carlos',
            apellidos='Pérez González',
            cedula='1234567890',
            fecha_nacimiento=date(1990, 5, 15),
            genero='M',
            telefono='099-123456',
            email='juan.perez@email.com',
            direccion='Calle Principal 123',
            tipo_sangre='O+',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.assertEqual(paciente.nombres, 'Juan Carlos')
        self.assertEqual(paciente.apellidos, 'Pérez González')
        self.assertEqual(paciente.cedula, '1234567890')
        self.assertEqual(paciente.genero, 'M')
        self.assertEqual(paciente.tipo_sangre, 'O+')
        self.assertEqual(paciente.clinica, self.clinica)
    
    def test_paciente_str_representation(self):
        """Test: Representación en string del paciente"""
        paciente = Paciente.objects.create(
            nombres='María',
            apellidos='López',
            cedula='0987654321',
            fecha_nacimiento=date(1985, 8, 20),
            genero='F',
            telefono='098-765432',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.assertEqual(str(paciente), 'López, María - 0987654321')
    
    def test_paciente_get_edad(self):
        """Test: Cálculo de edad del paciente"""
        # Paciente nacido hace exactamente 30 años
        from datetime import date as date_class
        today = date_class.today()
        fecha_nacimiento = date_class(today.year - 30, today.month, today.day)
        
        paciente = Paciente.objects.create(
            nombres='Pedro',
            apellidos='Sánchez',
            cedula='1111111111',
            fecha_nacimiento=fecha_nacimiento,
            genero='M',
            telefono='099-111111',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.assertEqual(paciente.get_edad(), 30)
    
    def test_paciente_get_nombre_completo(self):
        """Test: Obtener nombre completo del paciente"""
        paciente = Paciente.objects.create(
            nombres='Ana María',
            apellidos='Rodríguez Torres',
            cedula='2222222222',
            fecha_nacimiento=date(1995, 3, 10),
            genero='F',
            telefono='098-222222',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.assertEqual(paciente.get_nombre_completo(), 'Ana María Rodríguez Torres')
    
    def test_paciente_cedula_unica(self):
        """Test: La cédula debe ser única"""
        Paciente.objects.create(
            nombres='Luis',
            apellidos='Martínez',
            cedula='3333333333',
            fecha_nacimiento=date(1980, 1, 1),
            genero='M',
            telefono='099-333333',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Paciente.objects.create(
                nombres='Carlos',
                apellidos='García',
                cedula='3333333333',  # Cédula duplicada
                fecha_nacimiento=date(1992, 6, 15),
                genero='M',
                telefono='098-444444',
                clinica=self.clinica,
                uc=self.admin_user,
                um=self.admin_user.id
            )
    
    def test_paciente_cedula_formato_invalido(self):
        """Test: Formato de cédula inválido"""
        from django.core.exceptions import ValidationError
        
        paciente = Paciente(
            nombres='Laura',
            apellidos='Fernández',
            cedula='ABC1234567',  # Formato inválido
            fecha_nacimiento=date(1988, 9, 25),
            genero='F',
            telefono='099-555555',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError) as context:
            paciente.full_clean()
        
        self.assertIn('cedula', context.exception.message_dict)
    
    def test_paciente_fecha_nacimiento_futura(self):
        """Test: Fecha de nacimiento no puede ser futura"""
        from django.core.exceptions import ValidationError
        from datetime import date as date_class, timedelta
        
        fecha_futura = date_class.today() + timedelta(days=1)
        
        paciente = Paciente(
            nombres='Jorge',
            apellidos='Ramírez',
            cedula='4444444444',
            fecha_nacimiento=fecha_futura,
            genero='M',
            telefono='098-666666',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError) as context:
            paciente.full_clean()
        
        self.assertIn('fecha_nacimiento', context.exception.message_dict)
    
    def test_paciente_edad_invalida(self):
        """Test: Edad no puede ser mayor a 150 años"""
        from django.core.exceptions import ValidationError
        from datetime import date as date_class
        
        fecha_muy_antigua = date_class(1800, 1, 1)
        
        paciente = Paciente(
            nombres='Matusalén',
            apellidos='Anciano',
            cedula='5555555555',
            fecha_nacimiento=fecha_muy_antigua,
            genero='M',
            telefono='099-777777',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError) as context:
            paciente.full_clean()
        
        self.assertIn('fecha_nacimiento', context.exception.message_dict)
    
    def test_paciente_telefono_invalido(self):
        """Test: Teléfono debe tener mínimo 7 dígitos"""
        from django.core.exceptions import ValidationError
        
        paciente = Paciente(
            nombres='Elena',
            apellidos='Vargas',
            cedula='6666666666',
            fecha_nacimiento=date(1993, 12, 5),
            genero='F',
            telefono='123',  # Muy corto
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        with self.assertRaises(ValidationError) as context:
            paciente.full_clean()
        
        self.assertIn('telefono', context.exception.message_dict)
    
    def test_paciente_con_informacion_medica(self):
        """Test: Paciente con información médica completa"""
        paciente = Paciente.objects.create(
            nombres='Roberto',
            apellidos='Castro',
            cedula='7777777777',
            fecha_nacimiento=date(1975, 4, 18),
            genero='M',
            telefono='099-888888',
            email='roberto.castro@email.com',
            direccion='Av. Secundaria 456',
            tipo_sangre='AB+',
            alergias='Penicilina, Polen',
            observaciones_medicas='Hipertensión controlada',
            contacto_emergencia_nombre='María Castro',
            contacto_emergencia_telefono='098-999999',
            contacto_emergencia_relacion='Esposa',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        self.assertEqual(paciente.alergias, 'Penicilina, Polen')
        self.assertEqual(paciente.observaciones_medicas, 'Hipertensión controlada')
        self.assertEqual(paciente.contacto_emergencia_nombre, 'María Castro')
        self.assertEqual(paciente.contacto_emergencia_relacion, 'Esposa')
    
    def test_paciente_delete_clinica_protegido(self):
        """Test: No se puede eliminar una clínica con pacientes"""
        Paciente.objects.create(
            nombres='Sofía',
            apellidos='Morales',
            cedula='8888888888',
            fecha_nacimiento=date(1991, 7, 22),
            genero='F',
            telefono='098-111111',
            clinica=self.clinica,
            uc=self.admin_user,
            um=self.admin_user.id
        )
        
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.clinica.delete()
