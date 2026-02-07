"""
Tests para endpoints AJAX del módulo de citas.
Cubre validación de disponibilidad y carga de datos dinámicos.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta

from cit.models import (
    Clinica, Sucursal, Especialidad, Cubiculo,
    Dentista, Paciente, Cita
)
from cit.tests.base import MultiTenantTestCase


class CheckDentistaDisponibilidadTest(MultiTenantTestCase):
    """Tests para endpoint check_dentista_disponibilidad"""

    def setUp(self):
        """Configuración inicial"""
        super().setUp()  # Get multi-tenant context

        # Crear datos de prueba
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Calle Test',
            telefono='02-7654321',
            horario_apertura='08:00',
            horario_cierre='20:00',
            dias_atencion='Lunes a Sábado',
            uc=self.user,
            um=self.user.id
        )

        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Test',
            duracion_default=60,
            color_calendario='#FF5733',
            uc=self.user,
            um=self.user.id
        )

        self.cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            numero=1,
            capacidad=2,
            equipamiento='Test',
            uc=self.user,
            um=self.user.id
        )

        user_dentista = User.objects.create_user(
            username='drdentista',
            password='testpass123',
            first_name='María',
            last_name='García'
        )

        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            sucursal_principal=self.sucursal,
            cedula_profesional='12345',
            numero_licencia='LIC-001',
            telefono_movil='0999999999',
            fecha_contratacion='2020-01-15',
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.especialidad)

        self.paciente = Paciente.objects.create(
            nombres='Carlos',
            apellidos='Rodríguez',
            cedula='0912345678',
            fecha_nacimiento='1990-01-15',
            genero='M',
            email='carlos@test.com',
            telefono='0987654321',
            direccion='Av. Test',
            contacto_emergencia_nombre='Ana',
            contacto_emergencia_telefono='0991234567',
            contacto_emergencia_relacion='Madre',
            clinica=clinica,
            uc=self.user,
            um=self.user.id
        )

        # Fecha de referencia (mañana a las 10:00)
        self.fecha_valida = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

    def test_dentista_disponible(self):
        """Test: Dentista disponible en horario libre"""
        response = self.client.get('/cit/api/disponibilidad/dentista/', {
            'dentista_id': self.dentista.id,
            'fecha_hora': self.fecha_valida.isoformat(),
            'duracion': 60
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['disponible'])
        self.assertIn('disponible', data['mensaje'].lower())

    def test_dentista_ocupado(self):
        """Test: Dentista ocupado con cita existente"""
        # Crear cita existente
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

        # Intentar verificar disponibilidad en horario solapado
        fecha_solapada = self.fecha_valida + timedelta(minutes=30)

        response = self.client.get('/cit/api/disponibilidad/dentista/', {
            'dentista_id': self.dentista.id,
            'fecha_hora': fecha_solapada.isoformat(),
            'duracion': 60
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['disponible'])
        self.assertIn('citas_solapadas', data)
        self.assertEqual(len(data['citas_solapadas']), 1)

    def test_parametros_incompletos(self):
        """Test: Error con parámetros faltantes"""
        response = self.client.get('/cit/api/disponibilidad/dentista/', {
            'dentista_id': self.dentista.id
            # Falta fecha_hora
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['disponible'])
        self.assertIn('incompletos', data['mensaje'].lower())

    def test_dentista_no_existe(self):
        """Test: Error con dentista inexistente"""
        response = self.client.get('/cit/api/disponibilidad/dentista/', {
            'dentista_id': 99999,
            'fecha_hora': self.fecha_valida.isoformat(),
            'duracion': 60
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['disponible'])
        self.assertIn('error', data['mensaje'].lower())

    def test_excluir_cita_en_edicion(self):
        """Test: Al editar una cita, debe excluirse de la verificación"""
        # Crear cita
        cita = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=self.cubiculo,
            fecha_hora=self.fecha_valida,
            duracion=60,
            estado=Cita.ESTADO_PENDIENTE,
            uc=self.user,
            um=self.user.id
        )

        # Verificar disponibilidad de la misma cita (edición)
        response = self.client.get('/cit/api/disponibilidad/dentista/', {
            'dentista_id': self.dentista.id,
            'fecha_hora': self.fecha_valida.isoformat(),
            'duracion': 60,
            'cita_id': cita.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['disponible'])


class CheckCubiculoDisponibilidadTest(MultiTenantTestCase):
    """Tests para endpoint check_cubiculo_disponibilidad"""

    def setUp(self):
        """Configuración inicial"""
        super().setUp()  # Get multi-tenant context

        # Crear datos de prueba (similar a test anterior)
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Calle Test',
            telefono='02-7654321',
            horario_apertura='08:00',
            horario_cierre='20:00',
            dias_atencion='Lunes a Sábado',
            uc=self.user,
            um=self.user.id
        )

        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Test',
            duracion_default=60,
            color_calendario='#FF5733',
            uc=self.user,
            um=self.user.id
        )

        self.cubiculo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='Consultorio 1',
            numero=1,
            capacidad=2,
            equipamiento='Test',
            uc=self.user,
            um=self.user.id
        )


        user_dentista = User.objects.create_user(
            username='drdentista',
            password='testpass123',
            first_name='María',
            last_name='García'
        )

        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            sucursal_principal=self.sucursal,
            cedula_profesional='12345',
            numero_licencia='LIC-001',
            telefono_movil='0999999999',
            fecha_contratacion='2020-01-15',
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.especialidad)

        self.paciente = Paciente.objects.create(
            nombres='Carlos',
            apellidos='Rodríguez',
            cedula='0912345678',
            fecha_nacimiento='1990-01-15',
            genero='M',
            email='carlos@test.com',
            telefono='0987654321',
            direccion='Av. Test',
            contacto_emergencia_nombre='Ana',
            contacto_emergencia_telefono='0991234567',
            contacto_emergencia_relacion='Madre',
            clinica=clinica,
            uc=self.user,
            um=self.user.id
        )

        self.fecha_valida = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

    def test_cubiculo_disponible(self):
        """Test: Cubículo disponible en horario libre"""
        response = self.client.get('/cit/api/disponibilidad/cubiculo/', {
            'cubiculo_id': self.cubiculo.id,
            'fecha_hora': self.fecha_valida.isoformat(),
            'duracion': 60
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['disponible'])

    def test_cubiculo_ocupado(self):
        """Test: Cubículo ocupado con cita existente"""
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

        fecha_solapada = self.fecha_valida + timedelta(minutes=30)

        response = self.client.get('/cit/api/disponibilidad/cubiculo/', {
            'cubiculo_id': self.cubiculo.id,
            'fecha_hora': fecha_solapada.isoformat(),
            'duracion': 60
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['disponible'])
        self.assertIn('citas_solapadas', data)


class GetDentistaEspecialidadesTest(TestCase):
    """Tests para endpoint get_dentista_especialidades"""

    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Crear especialidades
        self.esp1 = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Test',
            duracion_default=60,
            color_calendario='#FF5733',
            uc=self.user,
            um=self.user.id
        )

        self.esp2 = Especialidad.objects.create(
            nombre='Endodoncia',
            descripcion='Test',
            duracion_default=90,
            color_calendario='#00FF00',
            uc=self.user,
            um=self.user.id
        )

        # Especialidad inactiva (no debería aparecer)
        self.esp_inactiva = Especialidad.objects.create(
            nombre='Inactiva',
            descripcion='Test',
            duracion_default=30,
            color_calendario='#0000FF',
            estado=False,
            uc=self.user,
            um=self.user.id
        )

        # Crear clinica y sucursal
        clinica = Clinica.objects.create(
            nombre='DentalForce Test',
            direccion='Av. Test',
            telefono='02-1234567',
            email='test@dentalforce.com',
            uc=self.user,
            um=self.user.id
        )

        sucursal = Sucursal.objects.create(
            clinica=clinica,
            nombre='Sucursal Test',
            direccion='Calle Test',
            telefono='02-7654321',
            horario_apertura='08:00',
            horario_cierre='20:00',
            dias_atencion='Lunes a Sábado',
            uc=self.user,
            um=self.user.id
        )

        # Crear dentista
        user_dentista = User.objects.create_user(
            username='drdentista',
            password='testpass123',
            first_name='María',
            last_name='García'
        )

        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            sucursal_principal=sucursal,
            cedula_profesional='12345',
            numero_licencia='LIC-001',
            telefono_movil='0999999999',
            fecha_contratacion='2020-01-15',
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.esp1, self.esp2, self.esp_inactiva)

    def test_obtener_especialidades_activas(self):
        """Test: Obtener solo especialidades activas del dentista"""
        response = self.client.get(f'/cit/api/dentista/{self.dentista.id}/especialidades/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['especialidades']), 2)  # Solo activas
        
        nombres = [esp['nombre'] for esp in data['especialidades']]
        self.assertIn('Ortodoncia', nombres)
        self.assertIn('Endodoncia', nombres)
        self.assertNotIn('Inactiva', nombres)

    def test_especialidades_tienen_datos_completos(self):
        """Test: Cada especialidad incluye todos los datos necesarios"""
        response = self.client.get(f'/cit/api/dentista/{self.dentista.id}/especialidades/')

        data = response.json()
        esp = data['especialidades'][0]
        
        self.assertIn('id', esp)
        self.assertIn('nombre', esp)
        self.assertIn('color', esp)
        self.assertIn('duracion_default', esp)

    def test_dentista_no_existe(self):
        """Test: Error con dentista inexistente"""
        response = self.client.get('/cit/api/dentista/99999/especialidades/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])


class CitasJsonTest(TestCase):
    """Tests para endpoint citas_json (FullCalendar)"""

    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Crear datos de prueba
        clinica = Clinica.objects.create(
            nombre='DentalForce Test',
            direccion='Av. Test',
            telefono='02-1234567',
            email='test@dentalforce.com',
            uc=self.user,
            um=self.user.id
        )

        sucursal = Sucursal.objects.create(
            clinica=clinica,
            nombre='Sucursal Test',
            direccion='Calle Test',
            telefono='02-7654321',
            horario_apertura='08:00',
            horario_cierre='20:00',
            dias_atencion='Lunes a Sábado',
            uc=self.user,
            um=self.user.id
        )

        self.especialidad = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Test',
            duracion_default=60,
            color_calendario='#FF5733',
            uc=self.user,
            um=self.user.id
        )

        cubiculo = Cubiculo.objects.create(
            sucursal=sucursal,
            nombre='Consultorio 1',
            numero=1,
            capacidad=2,
            equipamiento='Test',
            uc=self.user,
            um=self.user.id
        )

        user_dentista = User.objects.create_user(
            username='drdentista',
            password='testpass123',
            first_name='María',
            last_name='García'
        )

        self.dentista = Dentista.objects.create(
            usuario=user_dentista,
            sucursal_principal=sucursal,
            cedula_profesional='12345',
            numero_licencia='LIC-001',
            telefono_movil='0999999999',
            fecha_contratacion='2020-01-15',
            uc=self.user,
            um=self.user.id
        )
        self.dentista.especialidades.add(self.especialidad)

        self.paciente = Paciente.objects.create(
            nombres='Carlos',
            apellidos='Rodríguez',
            cedula='0912345678',
            fecha_nacimiento='1990-01-15',
            genero='M',
            email='carlos@test.com',
            telefono='0987654321',
            direccion='Av. Test',
            contacto_emergencia_nombre='Ana',
            contacto_emergencia_telefono='0991234567',
            contacto_emergencia_relacion='Madre',
            clinica=clinica,
            uc=self.user,
            um=self.user.id
        )

        # Crear citas de prueba
        self.fecha_base = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        self.cita1 = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=cubiculo,
            fecha_hora=self.fecha_base,
            duracion=60,
            estado=Cita.ESTADO_CONFIRMADA,
            uc=self.user,
            um=self.user.id
        )

        self.cita2 = Cita.objects.create(
            paciente=self.paciente,
            dentista=self.dentista,
            especialidad=self.especialidad,
            cubiculo=cubiculo,
            fecha_hora=self.fecha_base + timedelta(hours=2),
            duracion=30,
            estado=Cita.ESTADO_PENDIENTE,
            uc=self.user,
            um=self.user.id
        )

    def test_obtener_todas_las_citas(self):
        """Test: Obtener todas las citas sin filtros"""
        response = self.client.get('/cit/api/citas.json')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

    def test_formato_fullcalendar(self):
        """Test: Verificar formato correcto para FullCalendar"""
        response = self.client.get('/cit/api/citas.json')
        data = response.json()
        
        evento = data[0]
        self.assertIn('id', evento)
        self.assertIn('title', evento)
        self.assertIn('start', evento)
        self.assertIn('end', evento)
        self.assertIn('backgroundColor', evento)
        self.assertIn('extendedProps', evento)

    def test_filtrar_por_rango_fechas(self):
        """Test: Filtrar citas por rango de fechas"""
        start = self.fecha_base.isoformat()
        end = (self.fecha_base + timedelta(hours=1)).isoformat()

        response = self.client.get('/cit/api/citas.json', {
            'start': start,
            'end': end
        })

        data = response.json()
        # Solo la primera cita debería estar en el rango
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.cita1.id)

    def test_filtrar_por_dentista(self):
        """Test: Filtrar citas por dentista"""
        response = self.client.get('/cit/api/citas.json', {
            'dentista_id': self.dentista.id
        })

        data = response.json()
        self.assertGreaterEqual(len(data), 2)
        
        for evento in data:
            self.assertEqual(
                evento['extendedProps']['dentista'],
                str(self.dentista)
            )

    def test_filtrar_por_estado(self):
        """Test: Filtrar citas por estado"""
        response = self.client.get('/cit/api/citas.json', {
            'estado': Cita.ESTADO_CONFIRMADA
        })

        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        
        for evento in data:
            self.assertEqual(
                evento['extendedProps']['estado_codigo'],
                Cita.ESTADO_CONFIRMADA
            )

    def test_colores_por_estado(self):
        """Test: Verificar colores diferentes según estado"""
        response = self.client.get('/cit/api/citas.json')
        data = response.json()

        # Buscar cita confirmada y pendiente
        confirmada = next(e for e in data if e['id'] == self.cita1.id)
        pendiente = next(e for e in data if e['id'] == self.cita2.id)

        # Deben tener colores diferentes
        self.assertNotEqual(
            confirmada['backgroundColor'],
            pendiente['backgroundColor']
        )

    def test_extended_props_completos(self):
        """Test: ExtendedProps contiene toda la información necesaria"""
        response = self.client.get('/cit/api/citas.json')
        data = response.json()
        
        props = data[0]['extendedProps']
        
        campos_requeridos = [
            'paciente', 'paciente_cedula', 'dentista', 'especialidad',
            'especialidad_color', 'cubiculo', 'estado', 'estado_codigo',
            'duracion', 'duracion_display', 'observaciones'
        ]
        
        for campo in campos_requeridos:
            self.assertIn(campo, props)
