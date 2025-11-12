from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import json

from cit.models import (
    Clinica, Sucursal, Especialidad, Cubiculo, 
    Dentista, Paciente, Cita
)


class CitaViewsTestCase(TestCase):
    """Tests para las vistas de Citas"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.client = Client()
        
        # Crear usuario para autenticación
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Crear clínica
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle Principal 123',
            telefono='0987654321',
            email='test@clinica.com',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear sucursal
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Centro',
            direccion='Av. Central 456',
            telefono='0987654322',
            horario_apertura=datetime.strptime('08:00', '%H:%M').time(),
            horario_cierre=datetime.strptime('18:00', '%H:%M').time(),
            uc=self.user,
            um=self.user.id
        )
        
        # Crear especialidad
        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Especialidad en ortodoncia',
            duracion_default=60,
            color_calendario='#FF5733',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear cubículo
        self.cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            numero=1,
            equipamiento='Equipo completo de ortodoncia',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear usuario dentista
        self.user_dentista = User.objects.create_user(
            username='drdentista',
            password='dentista123',
            first_name='Roberto',
            last_name='Soto'
        )
        
        # Crear dentista
        self.dentista = Dentista.objects.create(
            usuario=self.user_dentista,
            cedula_profesional='1234567890',
            numero_licencia='REG-001',
            telefono_movil='0987654323',
            fecha_contratacion='2020-01-01',
            sucursal_principal=self.sucursal,
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.especialidad)
        
        # Crear paciente
        self.paciente = Paciente.objects.create(
            nombres='Juan Carlos',
            apellidos='Pérez González',
            cedula='0987654321',
            fecha_nacimiento='1990-01-15',
            genero='M',
            telefono='0987654324',
            email='juan@example.com',
            direccion='Calle Secundaria 789',
            contacto_emergencia_nombre='Ana Pérez',
            contacto_emergencia_telefono='0991234567',
            contacto_emergencia_relacion='Madre',
            clinica=self.clinica,
            uc=self.user,
            um=self.user.id
        )
        
        # Crear cita de prueba
        fecha_futura = timezone.now() + timedelta(days=7)
        self.cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=fecha_futura,
            duracion=60,
            estado=Cita.ESTADO_PENDIENTE,
            observaciones='Cita de prueba',
            uc=self.user,
            um=self.user.id
        )
    
    def test_cita_list_view_requires_login(self):
        """Test que la vista de lista requiere autenticación"""
        response = self.client.get(reverse('cit:cita-list'))
        self.assertEqual(response.status_code, 302)  # Redirección a login
    
    def test_cita_list_view_renders(self):
        """Test que la vista de lista se renderiza correctamente"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Citas')
        self.assertContains(response, self.paciente.nombres)
    
    def test_cita_list_view_filtro_estado(self):
        """Test filtro por estado en la lista"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-list') + '?estado=PEN')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.paciente.nombres)
    
    def test_cita_list_view_busqueda_paciente(self):
        """Test búsqueda por nombre de paciente"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-list') + '?q=Juan')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Carlos')
    
    def test_cita_detail_view_renders(self):
        """Test que la vista de detalle se renderiza correctamente"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-detail', kwargs={'pk': self.cita.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detalle de Cita')
        self.assertContains(response, self.paciente.nombres)
        self.assertContains(response, self.dentista.usuario.first_name)
    
    def test_cita_create_view_get(self):
        """Test GET del formulario de crear cita"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nueva Cita')
    
    def test_cita_create_view_post_valid(self):
        """Test POST válido para crear cita"""
        self.client.login(username='testuser', password='testpass123')
        
        fecha_futura = timezone.now() + timedelta(days=14)
        fecha_str = fecha_futura.strftime('%Y-%m-%dT%H:%M')
        
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'especialidad': self.especialidad.pk,
            'cubiculo': self.cubiculo.pk,
            'fecha_hora': fecha_str,
            'duracion': 30,
            'estado': Cita.ESTADO_PENDIENTE,
            'observaciones': 'Nueva cita de prueba'
        }
        
        response = self.client.post(reverse('cit:cita-create'), data)
        self.assertEqual(response.status_code, 302)  # Redirección exitosa
        
        # Verificar que se creó la cita
        nueva_cita = Cita.objects.filter(observaciones='Nueva cita de prueba').first()
        self.assertIsNotNone(nueva_cita)
        self.assertEqual(nueva_cita.paciente, self.paciente)
    
    def test_cita_create_view_post_invalid(self):
        """Test POST con datos inválidos (fecha en el pasado)"""
        self.client.login(username='testuser', password='testpass123')
        
        fecha_pasada = timezone.now() - timedelta(days=1)
        fecha_str = fecha_pasada.strftime('%Y-%m-%dT%H:%M')
        
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'especialidad': self.especialidad.pk,
            'cubiculo': self.cubiculo.pk,
            'fecha_hora': fecha_str,
            'duracion': 30,
            'estado': Cita.ESTADO_PENDIENTE
        }
        
        response = self.client.post(reverse('cit:cita-create'), data)
        self.assertEqual(response.status_code, 200)  # Se queda en el formulario
        self.assertFormError(response, 'form', 'fecha_hora', 
                           'La fecha y hora de la cita no puede ser en el pasado')
    
    def test_cita_update_view_get(self):
        """Test GET del formulario de editar cita"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-update', kwargs={'pk': self.cita.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Cita')
    
    def test_cita_update_view_post(self):
        """Test POST para editar cita"""
        self.client.login(username='testuser', password='testpass123')
        
        fecha_futura = timezone.now() + timedelta(days=10)
        fecha_str = fecha_futura.strftime('%Y-%m-%dT%H:%M')
        
        data = {
            'paciente': self.paciente.pk,
            'dentista': self.dentista.pk,
            'especialidad': self.especialidad.pk,
            'cubiculo': self.cubiculo.pk,
            'fecha_hora': fecha_str,
            'duracion': 45,
            'estado': Cita.ESTADO_CONFIRMADA,
            'observaciones': 'Observaciones actualizadas'
        }
        
        response = self.client.post(reverse('cit:cita-update', kwargs={'pk': self.cita.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar actualización
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.duracion, 45)
        self.assertEqual(self.cita.estado, Cita.ESTADO_CONFIRMADA)
    
    def test_cita_cancel_view_get(self):
        """Test GET de la vista de cancelación"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-cancel', kwargs={'pk': self.cita.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cancelar Cita')
        self.assertContains(response, 'motivo de cancelación')
    
    def test_cita_cancel_view_post(self):
        """Test POST para cancelar cita"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'motivo_cancelacion': 'Paciente solicitó reprogramación por viaje imprevisto'
        }
        
        response = self.client.post(reverse('cit:cita-cancel', kwargs={'pk': self.cita.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el estado cambió a CANCELADA
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, Cita.ESTADO_CANCELADA)
        self.assertIn('viaje imprevisto', self.cita.motivo_cancelacion)
    
    def test_confirmar_cita(self):
        """Test acción de confirmar cita"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-confirmar', kwargs={'pk': self.cita.pk}))
        
        self.assertEqual(response.status_code, 302)
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, Cita.ESTADO_CONFIRMADA)
    
    def test_iniciar_atencion_cita(self):
        """Test acción de iniciar atención"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-iniciar', kwargs={'pk': self.cita.pk}))
        
        self.assertEqual(response.status_code, 302)
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, Cita.ESTADO_EN_ATENCION)
    
    def test_completar_cita(self):
        """Test acción de completar cita"""
        # Primero cambiar a EN_ATENCION
        self.cita.estado = Cita.ESTADO_EN_ATENCION
        self.cita.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-completar', kwargs={'pk': self.cita.pk}))
        
        self.assertEqual(response.status_code, 302)
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, Cita.ESTADO_COMPLETADA)
    
    def test_marcar_no_asistio(self):
        """Test acción de marcar como no asistió"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-no-asistio', kwargs={'pk': self.cita.pk}))
        
        self.assertEqual(response.status_code, 302)
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, Cita.ESTADO_NO_ASISTIO)
    
    def test_ajax_dentista_disponibilidad_disponible(self):
        """Test AJAX endpoint cuando dentista está disponible"""
        self.client.login(username='testuser', password='testpass123')
        
        fecha_futura = timezone.now() + timedelta(days=30)
        
        response = self.client.get(reverse('cit:ajax-dentista-disponibilidad'), {
            'dentista_id': self.dentista.pk,
            'fecha_hora': fecha_futura.isoformat(),
            'duracion': 60
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['disponible'])
    
    def test_ajax_dentista_disponibilidad_ocupado(self):
        """Test AJAX endpoint cuando dentista está ocupado"""
        self.client.login(username='testuser', password='testpass123')
        
        # Usar la misma fecha de la cita existente
        response = self.client.get(reverse('cit:ajax-dentista-disponibilidad'), {
            'dentista_id': self.dentista.pk,
            'fecha_hora': self.cita.fecha_hora.isoformat(),
            'duracion': 60
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['disponible'])
        self.assertIn('ya tiene una cita', data['mensaje'])
    
    def test_ajax_cubiculo_disponibilidad(self):
        """Test AJAX endpoint de disponibilidad de cubículo"""
        self.client.login(username='testuser', password='testpass123')
        
        fecha_futura = timezone.now() + timedelta(days=30)
        
        response = self.client.get(reverse('cit:ajax-cubiculo-disponibilidad'), {
            'cubiculo_id': self.cubiculo.pk,
            'fecha_hora': fecha_futura.isoformat(),
            'duracion': 60
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['disponible'])
    
    def test_ajax_get_dentista_especialidades(self):
        """Test AJAX endpoint para obtener especialidades del dentista"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('cit:ajax-dentista-especialidades', kwargs={'dentista_id': self.dentista.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['especialidades']), 1)
        self.assertEqual(data['especialidades'][0]['nombre'], 'Ortodoncia')
    
    def test_cita_update_completada_solo_observaciones(self):
        """Test que una cita completada solo permite editar observaciones"""
        # Cambiar cita a completada
        self.cita.estado = Cita.ESTADO_COMPLETADA
        self.cita.save()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cit:cita-update', kwargs={'pk': self.cita.pk}))
        
        self.assertEqual(response.status_code, 200)
        # Verificar que los campos están deshabilitados (form.fields[name].disabled)
        self.assertContains(response, 'disabled')
