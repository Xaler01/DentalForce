from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from clinicas.models import Clinica
from pacientes.models import Paciente


class PacientesTenantViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()
        self.client.login(username='tester', password='pass')

        # Clínicas
        self.clinica_a = Clinica.objects.create(
            nombre='Clinica A', direccion='Dir A', telefono='099999999', email='a@test.local', uc=self.user
        )
        self.clinica_b = Clinica.objects.create(
            nombre='Clinica B', direccion='Dir B', telefono='088888888', email='b@test.local', uc=self.user
        )

        # Pacientes en A y B
        self.pa_a1 = Paciente.objects.create(nombres='Ana', apellidos='A1', uc=self.user, clinica=self.clinica_a)
        self.pa_a2 = Paciente.objects.create(nombres='Alan', apellidos='A2', uc=self.user, clinica=self.clinica_a)
        self.pa_b1 = Paciente.objects.create(nombres='Beto', apellidos='B1', uc=self.user, clinica=self.clinica_b)

        # Activar clínica A en sesión
        session = self.client.session
        session['clinica_id'] = self.clinica_a.id
        session.save()

    def test_list_view_filtra_por_clinica(self):
        url = reverse('pacientes:paciente-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        nombres = [p.get_nombre_completo() for p in resp.context['pacientes']]
        self.assertIn('Ana A1', nombres)
        self.assertIn('Alan A2', nombres)
        self.assertNotIn('Beto B1', nombres)

    def test_detail_view_restringe_acceso_a_otras_clinicas(self):
        # Intentar acceder a paciente de otra clínica debe redirigir/404
        url_other = reverse('pacientes:paciente-detail', kwargs={'pk': self.pa_b1.id})
        resp_other = self.client.get(url_other)
        self.assertEqual(resp_other.status_code, 404)

        # Acceder al paciente de la clínica activa
        url_ok = reverse('pacientes:paciente-detail', kwargs={'pk': self.pa_a1.id})
        resp_ok = self.client.get(url_ok)
        self.assertEqual(resp_ok.status_code, 200)
