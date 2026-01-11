from django.test import TestCase
from django.contrib.auth.models import User

from clinicas.models import Clinica
from enfermedades.models import CategoriaEnfermedad, Enfermedad, ClinicaEnfermedad
from enfermedades.utils import enfermedades_para_clinica, nombre_enfermedad_para_clinica


class ClinicaEnfermedadOverrideTests(TestCase):
    def setUp(self):
        # Usuario para uc
        self.user = User.objects.create_user(username='tester', password='pass')

        # Clínicas
        self.clinica_a = Clinica.objects.create(
            nombre='Tio Alex', direccion='Dir A', telefono='099999999', email='a@example.com', uc=self.user
        )
        self.clinica_b = Clinica.objects.create(
            nombre='Madomed', direccion='Dir B', telefono='088888888', email='b@example.com', uc=self.user
        )

        # Categoría y Enfermedades
        self.cat = CategoriaEnfermedad.objects.create(
            nombre='Metabólicas', descripcion='Cat metab', uc=self.user
        )
        self.enf1 = Enfermedad.objects.create(
            categoria=self.cat,
            nombre='Diabetes Mellitus',
            codigo_cie10='E14',
            nivel_riesgo='ALTO',
            estado=True,
            uc=self.user
        )
        self.enf2 = Enfermedad.objects.create(
            categoria=self.cat,
            nombre='Hipotiroidismo',
            codigo_cie10='E03',
            nivel_riesgo='MEDIO',
            estado=True,
            uc=self.user
        )

        # Overrides: deshabilitar enf1 en clinica_b, ocultar enf2 en clinica_b
        ClinicaEnfermedad.objects.create(
            clinica=self.clinica_b,
            enfermedad=self.enf1,
            habilitada=False,
            uc=self.user
        )
        ClinicaEnfermedad.objects.create(
            clinica=self.clinica_b,
            enfermedad=self.enf2,
            ocultar=True,
            nombre_personalizado='Tiroides baja',
            uc=self.user
        )

    def test_enfermedades_para_clinica_respetan_overrides(self):
        # En clínica A: sin overrides, ambas deberían aparecer
        qs_a = enfermedades_para_clinica(self.clinica_a)
        self.assertEqual(set(qs_a.values_list('id', flat=True)), {self.enf1.id, self.enf2.id})

        # En clínica B: enf1 deshabilitada y enf2 oculta -> ninguna debería aparecer
        qs_b = enfermedades_para_clinica(self.clinica_b)
        self.assertEqual(set(qs_b.values_list('id', flat=True)), set())

    def test_nombre_personalizado_para_clinica(self):
        # Clínica B tiene nombre personalizado para enf2
        nombre_b_enf2 = nombre_enfermedad_para_clinica(self.enf2, self.clinica_b)
        self.assertEqual(nombre_b_enf2, 'Tiroides baja')

        # Clínica A no tiene override -> usa nombre global
        nombre_a_enf2 = nombre_enfermedad_para_clinica(self.enf2, self.clinica_a)
        self.assertEqual(nombre_a_enf2, 'Hipotiroidismo')

    def test_isolamiento_por_clinica(self):
        # Cambiar override en clinica_b no afecta clinica_a
        cfg_b_enf1 = ClinicaEnfermedad.objects.get(clinica=self.clinica_b, enfermedad=self.enf1)
        cfg_b_enf1.habilitada = True
        cfg_b_enf1.save()

        # Ahora, en clínica B debería incluir enf1
        ids_b = set(enfermedades_para_clinica(self.clinica_b).values_list('id', flat=True))
        self.assertIn(self.enf1.id, ids_b)

        # Clínica A sigue viendo ambas
        ids_a = set(enfermedades_para_clinica(self.clinica_a).values_list('id', flat=True))
        self.assertEqual(ids_a, {self.enf1.id, self.enf2.id})
