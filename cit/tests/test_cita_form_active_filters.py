from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from cit.forms import CitaForm
from cit.models import Cubiculo, Especialidad
from clinicas.models import Clinica, Sucursal
from pacientes.models import Paciente
from personal.models import Dentista


class CitaFormActiveFiltersTests(TestCase):
    """Ensure CitaForm only offers active entities in dropdowns."""

    def setUp(self):
        self.uc = User.objects.create_user(username='uc', password='test1234')

        self.clinica = Clinica.objects.create(
            nombre='Clinica Test',
            direccion='Dir',
            telefono='0999999999',
            email='c@test.com',
            uc=self.uc,
        )
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Dir',
            telefono='0888888888',
            email='s@test.com',
            uc=self.uc,
        )

        # Pacientes
        self.paciente_activo = Paciente.objects.create(
            nombres='Activo',
            apellidos='Paciente',
            cedula='1111',
            fecha_nacimiento=date(1990, 1, 1),
            genero='M',
            telefono='0777777777',
            email='a@test.com',
            direccion='Dir',
            uc=self.uc,
        )
        self.paciente_inactivo = Paciente.objects.create(
            nombres='Inactivo',
            apellidos='Paciente',
            cedula='2222',
            fecha_nacimiento=date(1990, 1, 1),
            genero='F',
            telefono='0666666666',
            email='i@test.com',
            direccion='Dir',
            estado=False,
            uc=self.uc,
        )

        # Especialidades
        self.especialidad_activa = Especialidad.objects.create(
            nombre='Activa',
            descripcion='desc',
            uc=self.uc,
        )
        self.especialidad_inactiva = Especialidad.objects.create(
            nombre='Inactiva',
            descripcion='desc',
            estado=False,
            uc=self.uc,
        )

        # Dentistas
        user_dent_act = User.objects.create_user(username='dent_act', password='x')
        user_dent_inact = User.objects.create_user(username='dent_inact', password='x')
        self.dentista_activo = Dentista.objects.create(
            usuario=user_dent_act,
            cedula_profesional='123-1',
            telefono_movil='0555555555',
            uc=self.uc,
        )
        self.dentista_activo.especialidades.add(self.especialidad_activa)

        self.dentista_inactivo = Dentista.objects.create(
            usuario=user_dent_inact,
            cedula_profesional='123-2',
            telefono_movil='0444444444',
            estado=False,
            uc=self.uc,
        )
        self.dentista_inactivo.especialidades.add(self.especialidad_activa)

        # Cubículos
        self.cubiculo_activo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='C1',
            numero=1,
            uc=self.uc,
        )
        self.cubiculo_inactivo = Cubiculo.objects.create(
            sucursal=self.sucursal,
            nombre='C2',
            numero=2,
            estado=False,
            uc=self.uc,
        )

    def test_only_active_entities_are_listed(self):
        form = CitaForm()

        pacientes = list(form.fields['paciente'].queryset.values_list('pk', flat=True))
        dentistas = list(form.fields['dentista'].queryset.values_list('pk', flat=True))
        especialidades = list(form.fields['especialidad'].queryset.values_list('pk', flat=True))
        cubiculos = list(form.fields['cubiculo'].queryset.values_list('pk', flat=True))

        self.assertEqual(pacientes, [self.paciente_activo.pk])
        self.assertEqual(dentistas, [self.dentista_activo.pk])
        self.assertEqual(especialidades, [self.especialidad_activa.pk])
        self.assertEqual(cubiculos, [self.cubiculo_activo.pk])
