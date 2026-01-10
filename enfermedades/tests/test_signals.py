"""Tests para signals de alertas (SOOD-80)."""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from enfermedades.models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente, AlertaPaciente
from pacientes.models import Paciente
from cit.models import Clinica


class SignalsAlertasTestCase(TestCase):
    """Verifica que las señales actualicen alertas automáticamente."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='signaluser',
            password='testpass123'
        )
        self.clinica = Clinica.objects.create(nombre='Clínica Signals', uc=self.user)
        self.paciente = Paciente.objects.create(
            nombres='Luis',
            apellidos='Martinez',
            cedula='1112223334',
            uc=self.user
        )
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='Cardio',
            descripcion='Cardio',
            uc=self.user
        )
        self.enf_critica = Enfermedad.objects.create(
            nombre='Infarto',
            categoria=self.categoria,
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            uc=self.user
        )
        self.enf_alta = Enfermedad.objects.create(
            nombre='Hipertensión',
            categoria=self.categoria,
            nivel_riesgo='ALTO',
            genera_alerta_roja=False,
            uc=self.user
        )

    def test_crea_alerta_por_enfermedad_critica(self):
        """Al crear enfermedad crítica se genera alerta roja automáticamente."""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )

        alerta = AlertaPaciente.objects.filter(paciente=self.paciente, es_activa=True).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_CRITICA')
        self.assertEqual(alerta.nivel, 'ROJO')

    def test_desactiva_alerta_al_eliminar_enfermedad(self):
        """Al eliminar la relación, las alertas activas se recalculan y se desactivan si no hay riesgos."""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_alta,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )

        alerta = AlertaPaciente.objects.filter(paciente=self.paciente, es_activa=True).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_ALTA')

        relacion.delete()  # Trigger post_delete

        alerta.refresh_from_db()
        self.assertFalse(alerta.es_activa)

    def test_alerta_por_cambio_vip(self):
        """Al marcar VIP al paciente se genera alerta correspondiente."""
        self.paciente.es_vip = True
        self.paciente.categoria_vip = 'PREMIUM'
        self.paciente.save()

        alerta = AlertaPaciente.objects.filter(paciente=self.paciente, es_activa=True).first()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.tipo, 'VIP_MANUAL')
        self.assertEqual(alerta.nivel, 'ROJO')
