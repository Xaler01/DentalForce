"""
Tests para el CRUD de Dentistas con gestión de horarios.
Incluye tests para formularios, vistas y formsets inline.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, time
from cit.models import (
    Dentista, Especialidad, Sucursal, Clinica,
    DisponibilidadDentista, ExcepcionDisponibilidad
)
from cit.forms import (
    DentistaForm, DisponibilidadDentistaForm,
    ExcepcionDisponibilidadForm
)


class DentistaFormTest(TestCase):
    """Tests para el formulario de Dentista"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear clínica y sucursal
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle 123',
            telefono='0999999999',
            email='clinica@test.com'
        )
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Norte',
            direccion='Av. Norte 456',
            telefono='0988888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0)
        )
        
        # Crear especialidades
        self.especialidad1 = Especialidad.objects.create(
            nombre='Ortodoncia',
            duracion_default=60,
            color_calendario='#3498db'
        )
        self.especialidad2 = Especialidad.objects.create(
            nombre='Endodoncia',
            duracion_default=45,
            color_calendario='#e74c3c'
        )
    
    def test_formulario_valido_creacion(self):
        """Test: formulario válido para crear dentista"""
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'username': 'jperez',
            'email': 'jperez@test.com',
            'password': 'test123456',
            'cedula_profesional': '1234567890',
            'numero_licencia': 'LIC-12345',
            'telefono_movil': '0987654321',
            'fecha_contratacion': date(2024, 1, 15),
            'especialidades': [self.especialidad1.id],
            'sucursal_principal': self.sucursal.id,
            'biografia': 'Dentista con 5 años de experiencia',
            'estado': True
        }
        
        form = DentistaForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Errores: {form.errors}")
    
    def test_formulario_cedula_duplicada(self):
        """Test: error si la cédula profesional ya existe"""
        # Crear dentista existente
        user = User.objects.create_user(username='existing', password='test123')
        Dentista.objects.create(
            usuario=user,
            cedula_profesional='1234567890',
            numero_licencia='LIC-00001',
            telefono_movil='0999999999',
            fecha_contratacion=date(2024, 1, 1),
            sucursal_principal=self.sucursal
        )
        
        # Intentar crear otro con la misma cédula
        form_data = {
            'first_name': 'María',
            'last_name': 'González',
            'username': 'mgonzalez',
            'email': 'mgonzalez@test.com',
            'password': 'test123456',
            'cedula_profesional': '1234567890',  # Duplicada
            'numero_licencia': 'LIC-99999',
            'telefono_movil': '0987654321',
            'fecha_contratacion': date(2024, 2, 1),
            'especialidades': [self.especialidad1.id],
            'sucursal_principal': self.sucursal.id,
            'estado': True
        }
        
        form = DentistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cedula_profesional', form.errors)
    
    def test_formulario_username_duplicado(self):
        """Test: error si el username ya existe"""
        User.objects.create_user(username='jperez', password='test123')
        
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'username': 'jperez',  # Duplicado
            'email': 'otro@test.com',
            'password': 'test123456',
            'cedula_profesional': '9999999999',
            'numero_licencia': 'LIC-88888',
            'telefono_movil': '0987654321',
            'fecha_contratacion': date(2024, 1, 15),
            'especialidades': [self.especialidad1.id],
            'sucursal_principal': self.sucursal.id,
            'estado': True
        }
        
        form = DentistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_formulario_sin_especialidades(self):
        """Test: error si no se seleccionan especialidades"""
        form_data = {
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'username': 'amartinez',
            'email': 'amartinez@test.com',
            'password': 'test123456',
            'cedula_profesional': '5555555555',
            'numero_licencia': 'LIC-55555',
            'telefono_movil': '0987654321',
            'fecha_contratacion': date(2024, 1, 15),
            'especialidades': [],  # Vacío
            'sucursal_principal': self.sucursal.id,
            'estado': True
        }
        
        form = DentistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('especialidades', form.errors)
    
    def test_formulario_fecha_contratacion_futura(self):
        """Test: error si la fecha de contratación es futura"""
        from datetime import timedelta
        fecha_futura = date.today() + timedelta(days=30)
        
        form_data = {
            'first_name': 'Carlos',
            'last_name': 'López',
            'username': 'clopez',
            'email': 'clopez@test.com',
            'password': 'test123456',
            'cedula_profesional': '7777777777',
            'numero_licencia': 'LIC-77777',
            'telefono_movil': '0987654321',
            'fecha_contratacion': fecha_futura,
            'especialidades': [self.especialidad1.id],
            'sucursal_principal': self.sucursal.id,
            'estado': True
        }
        
        form = DentistaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_contratacion', form.errors)


class DisponibilidadDentistaFormTest(TestCase):
    """Tests para el formulario de disponibilidad de dentista"""
    
    def test_formulario_disponibilidad_valido(self):
        """Test: formulario de disponibilidad válido"""
        form_data = {
            'dia_semana': 0,  # Lunes
            'hora_inicio': time(8, 0),
            'hora_fin': time(12, 0),
            'activo': True
        }
        
        form = DisponibilidadDentistaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_disponibilidad_hora_fin_antes_inicio(self):
        """Test: error si hora fin es antes de hora inicio"""
        form_data = {
            'dia_semana': 0,
            'hora_inicio': time(12, 0),
            'hora_fin': time(8, 0),  # Antes del inicio
            'activo': True
        }
        
        form = DisponibilidadDentistaForm(data=form_data)
        self.assertFalse(form.is_valid())


class ExcepcionDisponibilidadFormTest(TestCase):
    """Tests para el formulario de excepciones"""
    
    def test_formulario_excepcion_valido_todo_dia(self):
        """Test: formulario de excepción válido (todo el día)"""
        form_data = {
            'fecha_inicio': date(2024, 12, 25),
            'fecha_fin': date(2024, 12, 25),
            'tipo': 'FERIA',
            'motivo': 'Navidad',
            'todo_el_dia': True
        }
        
        form = ExcepcionDisponibilidadForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_excepcion_fecha_fin_antes_inicio(self):
        """Test: error si fecha fin es antes de fecha inicio"""
        form_data = {
            'fecha_inicio': date(2024, 12, 31),
            'fecha_fin': date(2024, 12, 25),  # Antes del inicio
            'tipo': 'VACA',
            'motivo': 'Vacaciones',
            'todo_el_dia': True
        }
        
        form = ExcepcionDisponibilidadForm(data=form_data)
        self.assertFalse(form.is_valid())


class DentistaViewsTest(TestCase):
    """Tests para las vistas de Dentista"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        
        # Crear datos de prueba
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle 123',
            telefono='0999999999',
            email='clinica@test.com'
        )
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Norte',
            direccion='Av. Norte 456',
            telefono='0988888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0)
        )
        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            duracion_default=60,
            color_calendario='#3498db'
        )
        
        # Crear dentista de prueba
        user_dentista = User.objects.create_user(
            username='dperez',
            password='test123',
            first_name='Pedro',
            last_name='Pérez'
        )
        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            cedula_profesional='1234567890',
            numero_licencia='LIC-12345',
            telefono_movil='0987654321',
            fecha_contratacion=date(2024, 1, 15),
            sucursal_principal=self.sucursal
        )
        self.dentista.especialidades.add(self.especialidad)
    
    def test_dentista_list_view(self):
        """Test: acceso a la vista de lista"""
        response = self.client.get(reverse('cit:dentista-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dr(a). Pedro Pérez')
    
    def test_dentista_create_view_get(self):
        """Test: acceso al formulario de creación"""
        response = self.client.get(reverse('cit:dentista-create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nuevo Dentista')
    
    def test_dentista_update_view_get(self):
        """Test: acceso al formulario de edición"""
        response = self.client.get(
            reverse('cit:dentista-update', kwargs={'pk': self.dentista.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Dentista')
        self.assertContains(response, 'Pedro Pérez')
    
    def test_dentista_delete_view_get(self):
        """Test: acceso a la confirmación de eliminación"""
        response = self.client.get(
            reverse('cit:dentista-delete', kwargs={'pk': self.dentista.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Desactivar Dentista')
        self.assertContains(response, 'Pedro Pérez')
    
    def test_dentista_delete_view_post(self):
        """Test: eliminar (soft delete) un dentista"""
        response = self.client.post(
            reverse('cit:dentista-delete', kwargs={'pk': self.dentista.pk}),
            follow=True
        )
        
        # Verificar redirección
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el dentista existe pero está inactivo
        self.dentista.refresh_from_db()
        self.assertFalse(self.dentista.estado)
    
    def test_dentista_list_filtro_especialidad(self):
        """Test: filtrar dentistas por especialidad"""
        response = self.client.get(
            reverse('cit:dentista-list') + f'?especialidad={self.especialidad.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedro Pérez')
    
    def test_dentista_list_busqueda(self):
        """Test: buscar dentistas por nombre"""
        response = self.client.get(
            reverse('cit:dentista-list') + '?q=Pedro'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedro Pérez')


class DentistaModelTest(TestCase):
    """Tests para el modelo Dentista"""
    
    def setUp(self):
        """Configuración inicial"""
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle 123',
            telefono='0999999999',
            email='clinica@test.com'
        )
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Norte',
            direccion='Av. Norte 456',
            telefono='0988888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0)
        )
        self.user = User.objects.create_user(
            username='dperez',
            password='test123',
            first_name='Pedro',
            last_name='Pérez'
        )
        self.dentista = Dentista.objects.create(
            usuario=self.user,
            cedula_profesional='1234567890',
            numero_licencia='LIC-12345',
            telefono_movil='0987654321',
            fecha_contratacion=date(2024, 1, 15),
            sucursal_principal=self.sucursal
        )
    
    def test_dentista_str(self):
        """Test: representación en string del dentista"""
        self.assertEqual(str(self.dentista), 'Dr(a). Pedro Pérez')
    
    def test_dentista_get_especialidades_nombres(self):
        """Test: obtener nombres de especialidades"""
        esp1 = Especialidad.objects.create(
            nombre='Ortodoncia',
            duracion_default=60,
            color_calendario='#3498db'
        )
        esp2 = Especialidad.objects.create(
            nombre='Endodoncia',
            duracion_default=45,
            color_calendario='#e74c3c'
        )
        
        self.dentista.especialidades.add(esp1, esp2)
        
        nombres = self.dentista.get_especialidades_nombres()
        self.assertIn('Ortodoncia', nombres)
        self.assertIn('Endodoncia', nombres)


class DisponibilidadDentistaModelTest(TestCase):
    """Tests para el modelo DisponibilidadDentista"""
    
    def setUp(self):
        """Configuración inicial"""
        clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle 123',
            telefono='0999999999',
            email='clinica@test.com'
        )
        sucursal = Sucursal.objects.create(
            clinica=clinica,
            nombre='Sucursal Norte',
            direccion='Av. Norte 456',
            telefono='0988888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0)
        )
        user = User.objects.create_user(username='dperez', password='test123')
        self.dentista = Dentista.objects.create(
            usuario=user,
            cedula_profesional='1234567890',
            numero_licencia='LIC-12345',
            telefono_movil='0987654321',
            fecha_contratacion=date(2024, 1, 15),
            sucursal_principal=sucursal
        )
    
    def test_crear_disponibilidad(self):
        """Test: crear disponibilidad de dentista"""
        disponibilidad = DisponibilidadDentista.objects.create(
            dentista=self.dentista,
            dia_semana=0,  # Lunes
            hora_inicio=time(8, 0),
            hora_fin=time(12, 0),
            activo=True
        )
        
        self.assertEqual(disponibilidad.dia_semana, 0)
        self.assertEqual(disponibilidad.hora_inicio, time(8, 0))
        self.assertEqual(disponibilidad.hora_fin, time(12, 0))
        self.assertTrue(disponibilidad.activo)
    
    def test_disponibilidad_str(self):
        """Test: representación en string de disponibilidad"""
        disponibilidad = DisponibilidadDentista.objects.create(
            dentista=self.dentista,
            dia_semana=0,
            hora_inicio=time(8, 0),
            hora_fin=time(12, 0)
        )
        
        str_repr = str(disponibilidad)
        self.assertIn('Dr(a).', str_repr)
        self.assertIn('Lunes', str_repr)
        self.assertIn('08:00', str_repr)
        self.assertIn('12:00', str_repr)


class ExcepcionDisponibilidadModelTest(TestCase):
    """Tests para el modelo ExcepcionDisponibilidad"""
    
    def setUp(self):
        """Configuración inicial"""
        clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle 123',
            telefono='0999999999',
            email='clinica@test.com'
        )
        sucursal = Sucursal.objects.create(
            clinica=clinica,
            nombre='Sucursal Norte',
            direccion='Av. Norte 456',
            telefono='0988888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0)
        )
        user = User.objects.create_user(username='dperez', password='test123')
        self.dentista = Dentista.objects.create(
            usuario=user,
            cedula_profesional='1234567890',
            numero_licencia='LIC-12345',
            telefono_movil='0987654321',
            fecha_contratacion=date(2024, 1, 15),
            sucursal_principal=sucursal
        )
    
    def test_crear_excepcion_todo_dia(self):
        """Test: crear excepción de disponibilidad (todo el día)"""
        excepcion = ExcepcionDisponibilidad.objects.create(
            dentista=self.dentista,
            fecha_inicio=date(2024, 12, 25),
            fecha_fin=date(2024, 12, 25),
            tipo='FERIA',
            motivo='Navidad',
            todo_el_dia=True
        )
        
        self.assertEqual(excepcion.tipo, 'FERIA')
        self.assertTrue(excepcion.todo_el_dia)
        self.assertEqual(excepcion.motivo, 'Navidad')
    
    def test_excepcion_str(self):
        """Test: representación en string de excepción"""
        excepcion = ExcepcionDisponibilidad.objects.create(
            dentista=self.dentista,
            fecha_inicio=date(2024, 12, 25),
            fecha_fin=date(2024, 12, 26),
            tipo='VACA',
            motivo='Vacaciones de fin de año'
        )
        
        str_repr = str(excepcion)
        self.assertIn('Dr(a).', str_repr)
        self.assertIn('Vacaciones', str_repr)
