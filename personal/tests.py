from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from cit.models import Clinica, Sucursal, Especialidad
from .models import (
	Dentista,
	ComisionDentista,
	DisponibilidadDentista,
	ExcepcionDisponibilidad,
)


class BasePersonalTestCase(TestCase):
	"""Base con fixtures mínimas para los tests del app personal."""

	def setUp(self):
		self.user = User.objects.create_user(
			username="admin",
			password="testpass123",
			email="admin@test.com",
		)

		self.clinica = Clinica.objects.create(
			nombre="Clinica Test",
			ruc="1234567890001",
			direccion="Dir test",
			telefono="0999999999",
			email="clinic@test.com",
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		self.sucursal = Sucursal.objects.create(
			clinica=self.clinica,
			nombre="Sucursal Test",
			direccion="Dir sucursal",
			telefono="0999999999",
			email="sucursal@test.com",
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		self.especialidad = Especialidad.objects.create(
			nombre="General",
			duracion_default=60,
			color_calendario="#00ff00",
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		self.dentista_user = User.objects.create_user(
			username="dentista",
			password="testpass123",
			first_name="Ana",
			last_name="Perez",
		)

		self.dentista = Dentista.objects.create(
			usuario=self.dentista_user,
			cedula_profesional="123-456",
			telefono_movil="0999888777",
			sucursal_principal=self.sucursal,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		self.dentista.especialidades.add(self.especialidad)


class DentistaModelTest(BasePersonalTestCase):
	def test_legacy_kwargs_mapping(self):
		otro_usuario = User.objects.create_user(
			username="dentista2",
			password="testpass123",
			first_name="Luis",
			last_name="Moran",
		)
		dent = Dentista(
			usuario=otro_usuario,
			cedula="111-222",
			telefono="0999777666",
			sucursal_principal=self.sucursal,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		dent.full_clean()
		dent.save()
		self.assertEqual(dent.cedula_profesional, "111-222")
		self.assertEqual(dent.telefono_movil, "0999777666")

	def test_cedula_profesional_invalida(self):
		self.dentista.cedula_profesional = "ABC123"
		with self.assertRaises(ValidationError):
			self.dentista.full_clean()

	def test_fecha_contratacion_futura(self):
		self.dentista.fecha_contratacion = date.today() + timedelta(days=1)
		with self.assertRaises(ValidationError):
			self.dentista.full_clean()


class ComisionDentistaModelTest(BasePersonalTestCase):
	def test_especialidad_no_asignada(self):
		otra_esp = Especialidad.objects.create(
			nombre="Endodoncia",
			duracion_default=30,
			color_calendario="#ff0000",
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		com = ComisionDentista(
			dentista=self.dentista,
			especialidad=otra_esp,
			tipo_comision="PORCENTAJE",
			porcentaje=Decimal("10.00"),
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			com.full_clean()

	def test_unica_activa_por_especialidad(self):
		ComisionDentista.objects.create(
			dentista=self.dentista,
			especialidad=self.especialidad,
			tipo_comision="PORCENTAJE",
			porcentaje=Decimal("10.00"),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		com = ComisionDentista(
			dentista=self.dentista,
			especialidad=self.especialidad,
			tipo_comision="PORCENTAJE",
			porcentaje=Decimal("5.00"),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			com.full_clean()

	def test_calcular_comision_porcentaje_y_fijo(self):
		com_pct = ComisionDentista.objects.create(
			dentista=self.dentista,
			especialidad=self.especialidad,
			tipo_comision="PORCENTAJE",
			porcentaje=Decimal("20.00"),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		com_fijo = ComisionDentista.objects.create(
			dentista=self.dentista,
			especialidad=self.especialidad,
			tipo_comision="FIJO",
			valor_fijo=Decimal("50.00"),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		self.assertEqual(com_pct.calcular_comision(Decimal("200")), Decimal("40.00"))
		self.assertEqual(com_fijo.calcular_comision(Decimal("200")), Decimal("50.00"))


class DisponibilidadDentistaModelTest(BasePersonalTestCase):
	def test_solapamiento_no_permitido(self):
		DisponibilidadDentista.objects.create(
			dentista=self.dentista,
			sucursal=self.sucursal,
			dia_semana=0,
			hora_inicio=time(9, 0),
			hora_fin=time(12, 0),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)

		solapada = DisponibilidadDentista(
			dentista=self.dentista,
			sucursal=self.sucursal,
			dia_semana=0,
			hora_inicio=time(11, 0),
			hora_fin=time(13, 0),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			solapada.full_clean()

	def test_hora_fin_mayor_a_inicio(self):
		disp = DisponibilidadDentista(
			dentista=self.dentista,
			sucursal=self.sucursal,
			dia_semana=1,
			hora_inicio=time(14, 0),
			hora_fin=time(13, 0),
			activo=True,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			disp.full_clean()


class ExcepcionDisponibilidadModelTest(BasePersonalTestCase):
	def test_fecha_inicio_no_puede_ser_mayor(self):
		exc = ExcepcionDisponibilidad(
			dentista=self.dentista,
			fecha_inicio=date(2025, 1, 10),
			fecha_fin=date(2025, 1, 5),
			tipo="VACA",
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			exc.full_clean()

	def test_horas_requeridas_si_no_es_todo_el_dia(self):
		exc = ExcepcionDisponibilidad(
			dentista=self.dentista,
			fecha_inicio=date(2025, 1, 5),
			fecha_fin=date(2025, 1, 5),
			tipo="LIBRE",
			todo_el_dia=False,
			estado=True,
			uc=self.user,
			um=self.user.id,
		)
		with self.assertRaises(ValidationError):
			exc.full_clean()

		exc.hora_inicio = time(10, 0)
		exc.hora_fin = time(9, 0)
		with self.assertRaises(ValidationError):
			exc.full_clean()
