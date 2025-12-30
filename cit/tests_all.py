"""
Tests para el módulo de Citas (CIT).
Incluye tests unitarios para modelos, vistas y endpoints AJAX.

Ejecutar con:
    python manage.py test cit
    python manage.py test cit.tests.MoverCitaEndpointTest
    python manage.py test cit.tests.MoverCitaEndpointTest.test_mover_cita_exitoso
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta, time
import json
import os

TEST_PASSWORD = os.environ.get('TEST_PASSWORD', 'testpass123')

from .models import (
    Clinica, Sucursal, Dentista, Especialidad, 
    Cubiculo, Paciente, Cita
)


class CitaModelTest(TestCase):
    """Tests para el modelo Cita"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Usuario de auditoría
        self.user = User.objects.create_user(
            username='testuser',
            password=TEST_PASSWORD,
            email='test@test.com'
        )
        
        # Clínica y sucursal
        self.clinica = Clinica.objects.create(
            nombre='Test Clinic',
            ruc='1234567890001',
            direccion='Test Address',
            telefono='0999999999',
            email='clinic@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Principal',
            direccion='Test Address',
            telefono='0999999999',
            email='sucursal@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        # Dentista
        self.dentista_user = User.objects.create_user(
            username='dentista1',
            password=TEST_PASSWORD,
            first_name='Juan',
            last_name='Pérez'
        )
        
        self.dentista = Dentista.objects.create(
            usuario=self.dentista_user,
            cedula='0987654321',
            telefono='0999888777',
            sucursal_principal=self.sucursal,
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        # Especialidad
        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Especialidad en ortodoncia',
            duracion_default=60,
            color_calendario='#007bff',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.dentista.especialidades.add(self.especialidad)
        
        # Cubículo
        self.cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            descripcion='Consultorio principal',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        # Paciente
        self.paciente = Paciente.objects.create(
            cedula='1234567890',
            nombres='María',
            apellidos='González',
            fecha_nacimiento='1990-01-01',
            sexo='F',
            telefono='0999666555',
            email='maria@test.com',
            direccion='Test Address',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
    
    def test_crear_cita(self):
        """Test: Crear una cita correctamente"""
        fecha_hora = timezone.now() + timedelta(days=1, hours=2)
        fecha_hora = fecha_hora.replace(hour=10, minute=0, second=0, microsecond=0)
        
        cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=fecha_hora,
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            observaciones='Test cita',
            uc=self.user,
            um=self.user.id
        )
        
        self.assertEqual(cita.paciente, self.paciente)
        self.assertEqual(cita.dentista, self.dentista)
        self.assertEqual(cita.estado, Cita.ESTADO_CONFIRMADA)
        self.assertEqual(cita.duracion, 60)
    
    def test_str_cita(self):
        """Test: String representation de Cita"""
        fecha_hora = timezone.now() + timedelta(days=1)
        cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=fecha_hora,
            duracion=60,
            estado=Cita.ESTADO_PENDIENTE,
            uc=self.user,
            um=self.user.id
        )
        
        expected = f"Cita #{cita.id} - {self.paciente} - {fecha_hora.strftime('%d/%m/%Y %H:%M')}"
        self.assertEqual(str(cita), expected)


class MoverCitaEndpointTest(TestCase):
    """
    Tests para el endpoint PATCH /cit/api/citas/<id>/mover/
    
    Cubre las 7 validaciones principales del endpoint:
    1. Cita no encontrada
    2. Estado válido (no cancelada/completada)
    3. Fecha no en el pasado
    4. Duración entre 15-240 minutos
    5. Horario laboral 08:00-20:00
    6. Disponibilidad del dentista
    7. Disponibilidad del cubículo
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Usuario autenticado
        self.user = User.objects.create_user(
            username='admin',
            password=TEST_PASSWORD,
            email='admin@test.com'
        )
        self.client.login(username='admin', password=TEST_PASSWORD)
        
        # Crear entidades necesarias
        self.clinica = Clinica.objects.create(
            nombre='Test Clinic',
            ruc='1234567890001',
            direccion='Test Address',
            telefono='0999999999',
            email='clinic@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Test Address',
            telefono='0999999999',
            email='sucursal@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        dentista_user = User.objects.create_user(
            username='dentista',
            first_name='Dr.',
            last_name='Test'
        )
        
        self.dentista = Dentista.objects.create(
            usuario=dentista_user,
            cedula='0987654321',
            telefono='0999888777',
            sucursal_principal=self.sucursal,
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.especialidad = Especialidad.objects.create(
            nombre='General',
            duracion_default=60,
            color_calendario='#007bff',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.dentista.especialidades.add(self.especialidad)
        
        self.cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        self.paciente = Paciente.objects.create(
            cedula='1234567890',
            nombres='Test',
            apellidos='Patient',
            fecha_nacimiento='1990-01-01',
            sexo='M',
            telefono='0999666555',
            email='patient@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        # Crear cita base para tests
        self.fecha_hora_base = timezone.now() + timedelta(days=2)
        self.fecha_hora_base = self.fecha_hora_base.replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        
        self.cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_hora_base,
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            observaciones='Cita de prueba',
            uc=self.user,
            um=self.user.id
        )
    
    def test_mover_cita_exitoso(self):
        """Test 1: Mover cita a horario válido"""
        nueva_fecha = self.fecha_hora_base + timedelta(hours=2)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['mensaje'], 'Cita reprogramada exitosamente')
        
        # Verificar que se actualizó en BD
        self.cita.refresh_from_db()
        self.assertEqual(
            self.cita.fecha_hora.replace(microsecond=0),
            nueva_fecha.replace(microsecond=0)
        )
    
    def test_mover_cita_no_encontrada(self):
        """Test 2: Error 404 cuando la cita no existe"""
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': 99999}),
            data=json.dumps({
                'fecha_hora': timezone.now().isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['mensaje'], 'Cita no encontrada')
    
    def test_mover_cita_cancelada(self):
        """Test 3: No permitir mover cita cancelada"""
        self.cita.estado = Cita.ESTADO_CANCELADA
        self.cita.save()
        
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Cancelada', data['mensaje'])
    
    def test_mover_cita_completada(self):
        """Test 4: No permitir mover cita completada"""
        self.cita.estado = Cita.ESTADO_COMPLETADA
        self.cita.save()
        
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Completada', data['mensaje'])
    
    def test_mover_cita_al_pasado(self):
        """Test 5: Validación - No permitir fecha en el pasado"""
        fecha_pasada = timezone.now() - timedelta(days=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': fecha_pasada.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('pasado', data['mensaje'])
    
    def test_mover_cita_duracion_minima(self):
        """Test 6: Validación - Duración mínima de 15 minutos"""
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 10  # Menos de 15
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('15 minutos', data['mensaje'])
    
    def test_mover_cita_duracion_maxima(self):
        """Test 7: Validación - Duración máxima de 240 minutos"""
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 300  # Más de 240
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('240 minutos', data['mensaje'])
    
    def test_mover_cita_antes_horario_laboral(self):
        """Test 8: Validación - Horario laboral inicia a las 08:00"""
        fecha_temprano = self.fecha_hora_base.replace(hour=7, minute=30)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': fecha_temprano.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('08:00', data['mensaje'])
    
    def test_mover_cita_despues_horario_laboral(self):
        """Test 9: Validación - Horario laboral termina a las 20:00"""
        fecha_tarde = self.fecha_hora_base.replace(hour=19, minute=30)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': fecha_tarde.isoformat(),
                'duracion': 60  # Terminaría a las 20:30
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('20:00', data['mensaje'])
    
    def test_mover_cita_solapamiento_dentista(self):
        """Test 10: Validación - Detectar solapamiento con otra cita del dentista"""
        # Crear otra cita para el mismo dentista
        otra_cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_hora_base + timedelta(hours=2),
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar mover la cita original al mismo horario
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': otra_cita.fecha_hora.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('dentista', data['mensaje'].lower())
    
    def test_mover_cita_solapamiento_cubiculo(self):
        """Test 11: Validación - Detectar solapamiento de cubículo"""
        # Crear otro dentista
        otro_dentista_user = User.objects.create_user(
            username='dentista2',
            first_name='Dra.',
            last_name='Test2'
        )
        
        otro_dentista = Dentista.objects.create(
            usuario=otro_dentista_user,
            cedula='0987654322',
            telefono='0999888778',
            sucursal_principal=self.sucursal,
            estado=True,
            uc=self.user,
            um=self.user.id
        )
        
        otro_dentista.especialidades.add(self.especialidad)
        
        # Crear cita con otro dentista pero mismo cubículo
        otra_cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=otro_dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,  # Mismo cubículo
            fecha_hora=self.fecha_hora_base + timedelta(hours=3),
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar mover al mismo horario (mismo cubículo, diferente dentista)
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': otra_cita.fecha_hora.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('cubículo', data['mensaje'].lower())
    
    def test_mover_cita_sin_fecha(self):
        """Test 12: Error cuando no se proporciona fecha_hora"""
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('fecha y hora', data['mensaje'])
    
    def test_mover_cita_json_invalido(self):
        """Test 13: Error con JSON mal formado"""
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data='{ invalid json }',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('JSON inválidos', data['mensaje'])
    
    def test_mover_cita_sin_autenticacion(self):
        """Test 14: Requiere autenticación"""
        self.client.logout()
        
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat(),
                'duracion': 60
            }),
            content_type='application/json'
        )
        
        # Debe redirigir al login (302) o denegar acceso (403)
        self.assertIn(response.status_code, [302, 403])
    
    def test_mover_cita_mantener_duracion_actual(self):
        """Test 15: Mantener duración actual si no se especifica"""
        nueva_fecha = self.fecha_hora_base + timedelta(hours=1)
        duracion_original = self.cita.duracion
        
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': nueva_fecha.isoformat()
                # Sin especificar duracion
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.duracion, duracion_original)
    
    def test_mover_cita_cambiar_solo_duracion(self):
        """Test 16: Cambiar solo la duración sin cambiar fecha"""
        response = self.client.patch(
            reverse('cit:mover-cita', kwargs={'pk': self.cita.pk}),
            data=json.dumps({
                'fecha_hora': self.fecha_hora_base.isoformat(),
                'duracion': 90  # Cambiar de 60 a 90
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.duracion, 90)


class CitaViewsTest(TestCase):
    """Tests para las vistas de Citas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_calendario_view_login_required(self):
        """Test: Calendario requiere login"""
        self.client.logout()
        response = self.client.get(reverse('cit:calendario-citas'))
        self.assertEqual(response.status_code, 302)  # Redirect a login
    
    def test_calendario_view_authenticated(self):
        """Test: Calendario accesible para usuario autenticado"""
        response = self.client.get(reverse('cit:calendario-citas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/calendario_citas.html')
    
    def test_citas_list_view(self):
        """Test: Vista de lista de citas"""
        response = self.client.get(reverse('cit:cita-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/cita_list.html')
