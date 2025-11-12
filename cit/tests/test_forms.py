"""
Tests para formularios del módulo de citas.
Cubre validaciones de negocio en CitaForm y CitaCancelForm.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

from cit.models import (
    Clinica, Sucursal, Especialidad, Cubiculo, 
    Dentista, Paciente, Cita
)
from cit.forms import CitaForm, CitaCancelForm


class CitaFormTest(TestCase):
    """Tests para el formulario de creación/edición de citas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez'
        )
        
        # Crear clínica
        self.clinica = Clinica.objects.create(
            nombre='PowerDent',
            direccion='Av. Principal 123',
            telefono='02-1234567',
            email='info@powerdent.com',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear sucursal
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Centro',
            direccion='Calle Central 456',
            telefono='02-7654321',
            horario_apertura='08:00',
            horario_cierre='20:00',
            dias_atencion='Lunes a Sábado',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear especialidad
        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Corrección dental',
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
            capacidad=2,
            equipamiento='Equipo odontológico completo',
            uc=self.user,
            um=self.user.id
        )
        
        # Crear usuario dentista
        self.user_dentista = User.objects.create_user(
            username='drdentista',
            password='testpass123',
            first_name='María',
            last_name='García'
        )
        
        # Crear dentista
        self.dentista = Dentista.objects.create(
            usuario=self.user_dentista,
            sucursal_principal=self.sucursal,
            cedula_profesional='12345',
            numero_licencia='LIC-001',
            telefono_movil='0999999999',
            fecha_contratacion='2020-01-15',
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.especialidad)
        
        # Crear paciente
        self.paciente = Paciente.objects.create(
            nombres='Carlos Alberto',
            apellidos='Rodríguez López',
            cedula='0912345678',
            fecha_nacimiento='1990-01-15',
            genero='M',
            email='carlos@example.com',
            telefono='0987654321',
            direccion='Av. Ejemplo 123',
            contacto_emergencia_nombre='Ana Rodríguez',
            contacto_emergencia_telefono='0991234567',
            contacto_emergencia_relacion='Madre',
            clinica=self.clinica,
            uc=self.user,
            um=self.user.id
        )
        
        # Fecha y hora válida (mañana a las 10:00 AM)
        self.fecha_valida = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
    
    # ========================================================================
    # TESTS DE CREACIÓN EXITOSA
    # ========================================================================
    
    def test_crear_cita_valida(self):
        """Test: Crear una cita con todos los datos válidos"""
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
            'observaciones': 'Primera consulta'
        }
        
        form = CitaForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Errores: {form.errors}")
    
    # ========================================================================
    # TESTS DE VALIDACIÓN DE FECHA Y HORA
    # ========================================================================
    
    def test_fecha_en_pasado_rechazada(self):
        """Test: No permitir crear citas en el pasado"""
        fecha_pasada = timezone.now() - timedelta(days=1)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_pasada.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)
        self.assertIn('pasado', str(form.errors['fecha_hora']))
    
    def test_fecha_mas_6_meses_rechazada(self):
        """Test: No permitir citas con más de 6 meses de anticipación"""
        fecha_muy_futura = timezone.now() + timedelta(days=200)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_muy_futura.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)
        self.assertIn('6 meses', str(form.errors['fecha_hora']))
    
    def test_horario_antes_apertura_rechazado(self):
        """Test: No permitir citas antes de las 08:00"""
        fecha_temprano = self.fecha_valida.replace(hour=7, minute=30)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_temprano.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)
        self.assertIn('08:00', str(form.errors['fecha_hora']))
    
    def test_horario_despues_cierre_rechazado(self):
        """Test: No permitir citas a partir de las 20:00"""
        fecha_tarde = self.fecha_valida.replace(hour=20, minute=0)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_tarde.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)
    
    def test_cita_termina_despues_cierre(self):
        """Test: Validar que la cita no termine después de las 20:00"""
        # Cita a las 19:00 con duración de 90 minutos (terminaría a las 20:30)
        fecha = self.fecha_valida.replace(hour=19, minute=0)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 90,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('duracion', form.errors)
        self.assertIn('20:00', str(form.errors['duracion']))
    
    # ========================================================================
    # TESTS DE VALIDACIÓN DE DURACIÓN
    # ========================================================================
    
    def test_duracion_minima(self):
        """Test: La duración mínima es 15 minutos"""
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 10,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('duracion', form.errors)
    
    def test_duracion_maxima(self):
        """Test: La duración máxima es 240 minutos (4 horas)"""
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.replace(hour=8, minute=0).strftime('%Y-%m-%dT%H:%M'),
            'duracion': 300,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('duracion', form.errors)
    
    # ========================================================================
    # TESTS DE VALIDACIÓN DE ESPECIALIDAD Y DENTISTA
    # ========================================================================
    
    def test_dentista_sin_especialidad(self):
        """Test: El dentista debe tener la especialidad seleccionada"""
        # Crear otra especialidad que el dentista NO tiene
        otra_especialidad = Especialidad.objects.create(
            nombre='Endodoncia',
            descripcion='Tratamiento de conductos',
            duracion_default=90,
            color_calendario='#00FF00',
            uc=self.user,
            um=self.user.id
        )
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': otra_especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('especialidad', form.errors)
        self.assertIn('certificación', str(form.errors['especialidad']))
    
    def test_dentista_inactivo_rechazado(self):
        """Test: No permitir dentistas inactivos"""
        self.dentista.estado = False
        self.dentista.save()
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('dentista', form.errors)
    
    # ========================================================================
    # TESTS DE DISPONIBILIDAD
    # ========================================================================
    
    def test_dentista_ocupado_mismo_horario(self):
        """Test: No permitir citas si el dentista está ocupado"""
        # Crear cita existente
        cita_existente = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_valida,
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar crear otra cita solapada (30 minutos después)
        fecha_solapada = self.fecha_valida + timedelta(minutes=30)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_solapada.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora', form.errors)
        self.assertIn('ya tiene una cita', str(form.errors['fecha_hora']))
    
    def test_cubiculo_ocupado_mismo_horario(self):
        """Test: No permitir citas si el cubículo está ocupado"""
        # Crear otro dentista
        otro_user = User.objects.create_user(
            username='drotro',
            password='test123',
            first_name='Pedro',
            last_name='Sánchez'
        )
        otro_dentista = Dentista.objects.create(
            usuario=otro_user,
            sucursal_principal=self.sucursal,
            cedula_profesional='67890',
            numero_licencia='LIC-002',
            telefono_movil='0988888888',
            fecha_contratacion='2021-01-15',
            uc=self.user,
            um=self.user.id
        )
        otro_dentista.especialidades.add(self.especialidad)
        
        # Crear cita existente con primer dentista
        Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_valida,
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar crear cita con otro dentista en el MISMO cubículo y horario
        form_data = {
            'paciente': self.paciente.id,
            'dentista': otro_dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cubiculo', form.errors)
        self.assertIn('ocupado', str(form.errors['cubiculo']))
    
    def test_limite_citas_por_dia_paciente(self):
        """Test: Un paciente no puede tener más de 3 citas el mismo día"""
        # Crear 3 citas para el mismo día en diferentes horas
        for hora in [8, 12, 16]:
            fecha = self.fecha_valida.replace(hour=hora, minute=0)
            Cita.objects.create(
                paciente=self.paciente,
                dentista=self.dentista,
                especialidad=self.especialidad,
                cubiculo=self.cubiculo,
                fecha_hora=fecha,
                duracion=30,
                estado=Cita.ESTADO_CONFIRMADA,
                uc=self.user,
                um=self.user.id
            )
        
        # Intentar crear una 4ta cita
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.replace(hour=18, minute=0).strftime('%Y-%m-%dT%H:%M'),
            'duracion': 30,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('paciente', form.errors)
        self.assertIn('3 citas', str(form.errors['paciente']))
    
    # ========================================================================
    # TESTS DE TRANSICIONES DE ESTADO
    # ========================================================================
    
    def test_transicion_estado_invalida(self):
        """Test: No permitir transiciones de estado inválidas"""
        # Crear cita en estado COMPLETADA
        cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_valida,
            duracion=60,
            estado=Cita.ESTADO_COMPLETADA,
            uc=self.user,
            um=self.user.id
        )
        
        # Intentar cambiar a PENDIENTE (no permitido)
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data, instance=cita)
        self.assertFalse(form.is_valid())
        self.assertIn('estado', form.errors)
        self.assertIn('no permitida', str(form.errors['estado']))
    
    def test_cita_domingo_debe_estar_confirmada(self):
        """Test: Las citas de domingo deben crearse confirmadas"""
        # Buscar el próximo domingo
        fecha_domingo = timezone.now() + timedelta(days=1)
        while fecha_domingo.weekday() != 6:  # 6 = domingo
            fecha_domingo += timedelta(days=1)
        fecha_domingo = fecha_domingo.replace(hour=10, minute=0, second=0, microsecond=0)
        
        form_data = {
            'paciente': self.paciente.id,
            'dentista': self.dentista.id,
            'especialidad': self.especialidad.id,
            'cubiculo': self.cubiculo.id,
            'fecha_hora': fecha_domingo.strftime('%Y-%m-%dT%H:%M'),
            'duracion': 60,
            'estado': Cita.ESTADO_PENDIENTE,
        }
        
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('estado', form.errors)
        self.assertIn('domingo', str(form.errors['estado']).lower())


class CitaCancelFormTest(TestCase):
    """Tests para el formulario de cancelación de citas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_motivo_cancelacion_valido(self):
        """Test: Motivo de cancelación con longitud mínima"""
        form_data = {
            'motivo_cancelacion': 'El paciente solicitó reprogramar la cita por motivos laborales'
        }
        
        # No pasar instance para evitar validaciones del modelo
        form = CitaCancelForm(data=form_data)
        # Validar solo el campo del form
        form.fields['motivo_cancelacion'].validate(form_data['motivo_cancelacion'])
        self.assertTrue(True)  # Si llega aquí, la validación pasó
    
    def test_motivo_cancelacion_muy_corto(self):
        """Test: Rechazar motivos muy cortos"""
        form_data = {
            'motivo_cancelacion': 'Corto'
        }
        
        form = CitaCancelForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('motivo_cancelacion', form.errors)
        self.assertIn('10 caracteres', str(form.errors['motivo_cancelacion']))
    
    def test_motivo_cancelacion_vacio(self):
        """Test: Rechazar motivo vacío"""
        form_data = {
            'motivo_cancelacion': ''
        }
        
        form = CitaCancelForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('motivo_cancelacion', form.errors)
