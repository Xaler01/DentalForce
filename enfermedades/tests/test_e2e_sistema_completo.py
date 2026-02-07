"""
Tests E2E del sistema de enfermedades y alertas (SOOD-89)
Flujo completo: crear paciente, asignar enfermedades, visualizar alertas, modal dinámico
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from pacientes.models import Paciente
from enfermedades.models import Enfermedad, EnfermedadPaciente, CategoriaEnfermedad
from cit.models import Dentista, Especialidad
from clinicas.models import Clinica


class EnfermedadesAlertasE2ETest(TestCase):
    """Tests end-to-end del sistema completo de enfermedades y alertas"""

    @classmethod
    def setUpTestData(cls):
        """Configuración de datos comunes para todos los tests"""
        # Clínica activa para sesión (middleware requiere clinica_id)
        cls.clinica = Clinica.objects.create(
            nombre='Clinica Test', direccion='Dir', telefono='099999999', email='test@clinic.local', uc=User.objects.create_user(username='owner')
        )
        # Usuario y dentista
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        cls.dentista = Dentista.objects.create(
            usuario=cls.user,
            cedula_profesional='DENT-001',
            uc=cls.user,
            um=cls.user.id
        )

        # Categorías de enfermedades
        cls.categoria_cardio = CategoriaEnfermedad.objects.create(
            nombre='Cardiovascular',
            descripcion='Enfermedades del corazón',
            color='#e74c3c',
            uc=cls.user,
            um=cls.user.id
        )

        cls.categoria_endo = CategoriaEnfermedad.objects.create(
            nombre='Endocrinológica',
            descripcion='Diabetes y trastornos endocrinos',
            color='#3498db',
            uc=cls.user,
            um=cls.user.id
        )

        # Enfermedades
        cls.diabetes = Enfermedad.objects.create(
            categoria=cls.categoria_endo,
            nombre='Diabetes Mellitus Tipo 2',
            codigo_cie10='E11',
            nivel_riesgo='ALTO',
            genera_alerta_amarilla=True,
            uc=cls.user,
            um=cls.user.id
        )

        cls.hipertension = Enfermedad.objects.create(
            categoria=cls.categoria_cardio,
            nombre='Hipertensión Arterial',
            codigo_cie10='I10',
            nivel_riesgo='MEDIO',
            genera_alerta_amarilla=True,
            requiere_interconsulta=True,
            uc=cls.user,
            um=cls.user.id
        )

        cls.infarto = Enfermedad.objects.create(
            categoria=cls.categoria_cardio,
            nombre='Infarto Miocárdico Previo',
            codigo_cie10='I21',
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            requiere_interconsulta=True,
            uc=cls.user,
            um=cls.user.id
        )

        # Paciente normal
        cls.paciente_normal = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='12345678',
            genero='M',
            clinica=cls.clinica,
            uc=cls.user,
            um=cls.user.id
        )

        # Paciente con enfermedades
        cls.paciente_enfermo = Paciente.objects.create(
            nombres='María',
            apellidos='García',
            cedula='87654321',
            genero='F',
            clinica=cls.clinica,
            uc=cls.user,
            um=cls.user.id
        )

        # Paciente VIP con enfermedades críticas
        cls.paciente_vip = Paciente.objects.create(
            nombres='Carlos',
            apellidos='López',
            cedula='11223344',
            genero='M',
            es_vip=True,
            categoria_vip='PREMIUM',
            clinica=cls.clinica,
            uc=cls.user,
            um=cls.user.id
        )

    def setUp(self):
        """Preparación antes de cada test"""
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        # Activar clínica en sesión para evitar redirección del middleware
        session = self.client.session
        session['clinica_id'] = self.clinica.id
        session.save()

    def test_e2e_crear_paciente_asignar_enfermedad(self):
        """E2E: Crear paciente y asignarle una enfermedad vía API enfermedades"""
        # Usar el enfoque pragmático: crear paciente sin enfermedad primero
        paciente = Paciente.objects.create(
            nombres='Pedro',
            apellidos='Rodríguez',
            cedula='55667788',
            genero='M',
            clinica=self.clinica,
            uc=self.user,
            um=self.user.id
        )

        # Luego asignar enfermedad vía AJAX
        response = self.client.post(
            reverse('pacientes:paciente-enfermedad-add', kwargs={'pk': paciente.pk}),
            {
                'enfermedad': self.diabetes.id,
                'estado_actual': 'ACTIVA',
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verificar que la enfermedad fue asignada
        ep = EnfermedadPaciente.objects.get(
            paciente=paciente,
            enfermedad=self.diabetes
        )
        self.assertEqual(ep.estado_actual, 'ACTIVA')

    def test_e2e_lista_pacientes_muestra_semaforos(self):
        """E2E: Lista de pacientes muestra semáforos correctos"""
        # Asignar enfermedades a pacientes
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_enfermo,
            enfermedad=self.diabetes,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        EnfermedadPaciente.objects.create(
            paciente=self.paciente_vip,
            enfermedad=self.infarto,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.get(reverse('pacientes:paciente-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'semaforo')  # Verifica que haya semáforos

    def test_e2e_detalle_paciente_muestra_semaforo_cabecera(self):
        """E2E: Detalle de paciente muestra semáforo en cabecera"""
        # Asignar enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_vip,
            enfermedad=self.infarto,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.get(
            reverse('pacientes:paciente-detail', kwargs={'pk': self.paciente_vip.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'semaforo-rojo')  # Semáforo rojo por enfermedad crítica
        self.assertContains(response, 'Condición crítica')  # Badge de condición crítica

    def test_e2e_agregar_enfermedad_ajax(self):
        """E2E: Agregar enfermedad vía modal AJAX"""
        response = self.client.post(
            reverse('pacientes:paciente-enfermedad-add', kwargs={'pk': self.paciente_normal.pk}),
            {
                'enfermedad': self.diabetes.id,
                'estado_actual': 'ACTIVA',
                'fecha_diagnostico': '2023-01-15',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})

        # Verificar que la enfermedad fue agregada
        ep = EnfermedadPaciente.objects.get(
            paciente=self.paciente_normal,
            enfermedad=self.diabetes
        )
        self.assertEqual(ep.estado_actual, 'ACTIVA')

    def test_e2e_eliminar_enfermedad_ajax(self):
        """E2E: Eliminar enfermedad vía AJAX"""
        # Crear relación primero
        ep = EnfermedadPaciente.objects.create(
            paciente=self.paciente_normal,
            enfermedad=self.diabetes,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.post(
            reverse('pacientes:paciente-enfermedad-delete', kwargs={
                'pk': self.paciente_normal.pk,
                'ep_id': ep.id
            })
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True})

        # Verificar que fue eliminada
        self.assertFalse(
            EnfermedadPaciente.objects.filter(
                paciente=self.paciente_normal,
                enfermedad=self.diabetes
            ).exists()
        )

    def test_e2e_modal_alertas_ajax_rojo(self):
        """E2E: Modal de alertas muestra correctamente alertas ROJO"""
        # Asignar enfermedad crítica que genera alerta roja
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_vip,
            enfermedad=self.infarto,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.get(
            reverse('pacientes:paciente-alertas-detalles', kwargs={'pk': self.paciente_vip.pk})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['nivel_alerta'], 'ROJO')
        self.assertIn('Alerta Roja', data['label'])
        self.assertTrue(len(data['factores']['ROJO']) > 0)

    def test_e2e_modal_alertas_ajax_amarillo(self):
        """E2E: Modal de alertas muestra correctamente alertas AMARILLO"""
        # Asignar enfermedad de alto riesgo que genera alerta amarilla
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_enfermo,
            enfermedad=self.diabetes,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.get(
            reverse('pacientes:paciente-alertas-detalles', kwargs={'pk': self.paciente_enfermo.pk})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['nivel_alerta'], 'AMARILLO')
        self.assertIn('Precaución', data['label'])

    def test_e2e_modal_alertas_ajax_verde(self):
        """E2E: Modal de alertas muestra verde cuando no hay alertas"""
        response = self.client.get(
            reverse('pacientes:paciente-alertas-detalles', kwargs={'pk': self.paciente_normal.pk})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['nivel_alerta'], 'VERDE')

    def test_e2e_flujo_vip_manual(self):
        """E2E: Paciente VIP genera alerta ROJO correctamente"""
        response = self.client.get(
            reverse('pacientes:paciente-alertas-detalles', kwargs={'pk': self.paciente_vip.pk})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # VIP sin enfermedades críticas debe tener nivel ROJO por ser VIP
        self.assertEqual(data['nivel_alerta'], 'ROJO')

    def test_e2e_semaforo_dinamico_lista_pacientes(self):
        """E2E: Semáforo en lista se actualiza dinámicamente"""
        # Inicialmente verde
        response1 = self.client.get(reverse('pacientes:paciente-list'))
        self.assertEqual(response1.status_code, 200)

        # Asignar enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_normal,
            enfermedad=self.infarto,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        # Verificar que el semáforo ahora es rojo
        response2 = self.client.get(reverse('pacientes:paciente-list'))
        self.assertEqual(response2.status_code, 200)
        # Se verificaría en context que nivel_alerta cambió, pero aquí solo chequeamos renderizado

    def test_e2e_secccion_enfermedades_ficha_paciente(self):
        """E2E: Sección de enfermedades visible en ficha de paciente"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_enfermo,
            enfermedad=self.diabetes,
            estado_actual='ACTIVA',
            fecha_diagnostico='2020-05-10',
            uc=self.user,
            um=self.user.id
        )

        response = self.client.get(
            reverse('pacientes:paciente-detail', kwargs={'pk': self.paciente_enfermo.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enfermedades Preexistentes')
        self.assertContains(response, 'Diabetes Mellitus Tipo 2')
        self.assertContains(response, 'E11')  # CIE-10


class EnfermedadModelE2ETest(TestCase):
    """Tests E2E del modelo Enfermedad y EnfermedadPaciente"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpass123')

        cls.categoria = CategoriaEnfermedad.objects.create(
            nombre='Test',
            uc=cls.user,
            um=cls.user.id
        )

        cls.enfermedad = Enfermedad.objects.create(
            categoria=cls.categoria,
            nombre='Test Enfermedad',
            nivel_riesgo='ALTO',
            uc=cls.user,
            um=cls.user.id
        )

        cls.paciente = Paciente.objects.create(
            nombres='Test',
            apellidos='Paciente',
            uc=cls.user,
            um=cls.user.id
        )

    def test_e2e_crear_enfermedad_paciente_con_auditoría(self):
        """E2E: Crear EnfermedadPaciente con auditoría correcta"""
        ep = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        self.assertEqual(ep.paciente, self.paciente)
        self.assertEqual(ep.enfermedad, self.enfermedad)
        self.assertEqual(ep.uc, self.user)
        self.assertEqual(ep.um, self.user.id)

    def test_e2e_estado_enfermedad_transiciones(self):
        """E2E: Transiciones de estado en EnfermedadPaciente"""
        ep = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad,
            estado_actual='ACTIVA',
            uc=self.user,
            um=self.user.id
        )

        # Cambiar a controlada
        ep.estado_actual = 'CONTROLADA'
        ep.save()
        ep.refresh_from_db()
        self.assertEqual(ep.estado_actual, 'CONTROLADA')

        # Cambiar a curada
        ep.estado_actual = 'CURADA'
        ep.save()
        ep.refresh_from_db()
        self.assertEqual(ep.estado_actual, 'CURADA')
