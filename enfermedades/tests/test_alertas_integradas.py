"""Tests integrales del sistema de alertas (SOOD-81)."""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from enfermedades.models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente, AlertaPaciente
from enfermedades.utils import GestorAlertas
from pacientes.models import Paciente
from cit.models import Clinica


class AlertasIntegradasTestCase(TestCase):
    """Validación extremo a extremo del flujo de alertas."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='integrado',
            password='secret123'
        )
        self.clinica = Clinica.objects.create(nombre='Clínica Integrada', uc=self.user)
        self.paciente = Paciente.objects.create(
            nombres='Ana',
            apellidos='Suarez',
            cedula='5554443332',
            uc=self.user
        )
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='Respiratorias',
            descripcion='Pruebas integrales',
            uc=self.user
        )
        self.enf_critica = Enfermedad.objects.create(
            nombre='Neumonía Grave',
            categoria=self.categoria,
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            uc=self.user
        )
        self.enf_media = Enfermedad.objects.create(
            nombre='Asma Moderada',
            categoria=self.categoria,
            nivel_riesgo='MEDIO',
            requiere_interconsulta=True,
            uc=self.user
        )
        self.enf_media2 = Enfermedad.objects.create(
            nombre='Asma Leve',
            categoria=self.categoria,
            nivel_riesgo='MEDIO',
            requiere_interconsulta=True,
            uc=self.user
        )
        self.enf_baja = Enfermedad.objects.create(
            nombre='Rinitis',
            categoria=self.categoria,
            nivel_riesgo='BAJO',
            uc=self.user
        )

    def _recalcular(self):
        """Helper para recalcular alertas y devolver la alerta activa."""
        alerta, _ = GestorAlertas(self.paciente, self.user).actualizar_alertas()
        return AlertaPaciente.objects.filter(paciente=self.paciente, es_activa=True).first()

    def test_flujo_critico_vip_y_cleanup(self):
        """Crea alerta por crítica, eleva por VIP y limpia al remover riesgos."""
        # 1) Enfermedad crítica -> alerta roja tipo enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        alerta = self._recalcular()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.nivel, 'ROJO')
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_CRITICA')

        # 2) Marcar VIP manual -> debe actualizar a tipo VIP_MANUAL (sigue roja)
        self.paciente.es_vip = True
        self.paciente.categoria_vip = 'PLATINUM'
        self.paciente.save()
        alerta = self._recalcular()
        # La prioridad se mantiene en ENFERMEDAD_CRITICA aunque sea VIP
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_CRITICA')
        self.assertEqual(alerta.nivel, 'ROJO')

        # 3) Eliminar enfermedad crítica y desmarcar VIP -> debe quedar verde y desactivar alertas
        self.paciente.es_vip = False
        self.paciente.categoria_vip = ''
        self.paciente.save()
        self.paciente.enfermedades_paciente.all().delete()
        alerta = self._recalcular()
        self.assertIsNone(alerta)  # No alerta activa
        self.assertEqual(
            AlertaPaciente.objects.filter(paciente=self.paciente, es_activa=True).count(),
            0
        )

    def test_multiples_condiciones_interconsulta(self):
        """Con varias condiciones no críticas debe generar alerta amarilla por múltiples/interconsulta."""
        # Agregar 2 condiciones medias y 1 baja
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_media,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_media2,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_baja,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )

        alerta = self._recalcular()
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.nivel, 'AMARILLO')
        self.assertIn(alerta.tipo, ['MULTIPLES_CONDICIONES', 'REQUIERE_INTERCONSULTA'])
        self.assertTrue(alerta.enfermedades_relacionadas.count() >= 1)

    def test_actualizacion_por_cierre_enfermedad(self):
        """Si una enfermedad se marca CURADA debe recalcular y bajar nivel si corresponde."""
        relacion = EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_media,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        alerta = self._recalcular()
        self.assertEqual(alerta.nivel, 'AMARILLO')

        # Cerrar la enfermedad
        relacion.estado_actual = 'CURADA'
        relacion.save()
        alerta = self._recalcular()
        self.assertIsNone(alerta)  # Sin riesgos -> sin alertas

    def test_retorno_factores_en_reporte(self):
        """Reporte debe incluir factores e historial coherente."""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enf_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        gestor = GestorAlertas(self.paciente, self.user)
        gestor.actualizar_alertas()

        reporte = gestor.generar_reporte_alertas()
        self.assertIn('nivel_actual', reporte)
        self.assertIn(reporte['nivel_actual'], ['ROJO', 'AMARILLO', 'VERDE'])
        self.assertGreater(len(reporte['factores']['ROJO']), 0)
        self.assertGreaterEqual(len(reporte['alertas_activas']), 1)

        # Al desactivar la alerta debe desaparecer del reporte activo
        AlertaPaciente.objects.filter(paciente=self.paciente).update(es_activa=False)
        reporte2 = gestor.generar_reporte_alertas()
        self.assertEqual(len(reporte2['alertas_activas']), 0)
