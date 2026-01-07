from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import generic
from django.db.models import Count, Q

from bases.views import SinPrivilegios
from pacientes.models import Paciente
from .models import CategoriaEnfermedad, Enfermedad, AlertaPaciente
from .forms import CategoriaEnfermedadForm, EnfermedadForm
from .utils import CalculadorAlerta


class CategoriaEnfermedadListView(SinPrivilegios, generic.ListView):
	"""Listado de categorías de enfermedades (SOOD-82)."""

	permission_required = "enfermedades.view_categoriaenfermedad"
	model = CategoriaEnfermedad
	template_name = "enfermedades/categoria_list.html"
	context_object_name = "categorias"
	ordering = ["orden", "nombre"]


class CategoriaEnfermedadCreateView(SuccessMessageMixin, SinPrivilegios, generic.CreateView):
	"""Crear categoría de enfermedad."""

	permission_required = "enfermedades.add_categoriaenfermedad"
	model = CategoriaEnfermedad
	form_class = CategoriaEnfermedadForm
	template_name = "enfermedades/categoria_form.html"
	success_url = reverse_lazy("enfermedades:categoria_list")
	success_message = "Categoría creada correctamente"

	def form_valid(self, form):
		form.instance.uc = self.request.user
		return super().form_valid(form)


class CategoriaEnfermedadUpdateView(SuccessMessageMixin, SinPrivilegios, generic.UpdateView):
	"""Editar categoría de enfermedad."""

	permission_required = "enfermedades.change_categoriaenfermedad"
	model = CategoriaEnfermedad
	form_class = CategoriaEnfermedadForm
	template_name = "enfermedades/categoria_form.html"
	success_url = reverse_lazy("enfermedades:categoria_list")
	success_message = "Categoría actualizada correctamente"

	def form_valid(self, form):
		form.instance.um = self.request.user.id
		return super().form_valid(form)


class CategoriaEnfermedadDeleteView(SuccessMessageMixin, SinPrivilegios, generic.DeleteView):
	"""Eliminar categoría de enfermedad."""

	permission_required = "enfermedades.delete_categoriaenfermedad"
	model = CategoriaEnfermedad
	template_name = "enfermedades/categoria_confirm_delete.html"
	success_url = reverse_lazy("enfermedades:categoria_list")
	success_message = "Categoría eliminada correctamente"


class EnfermedadListView(SinPrivilegios, generic.ListView):
	"""Listado de enfermedades."""

	permission_required = "enfermedades.view_enfermedad"
	model = Enfermedad
	template_name = "enfermedades/enfermedad_list.html"
	context_object_name = "enfermedades"
	ordering = ["categoria__nombre", "nombre"]


class EnfermedadCreateView(SuccessMessageMixin, SinPrivilegios, generic.CreateView):
	"""Crear enfermedad."""

	permission_required = "enfermedades.add_enfermedad"
	model = Enfermedad
	form_class = EnfermedadForm
	template_name = "enfermedades/enfermedad_form.html"
	success_url = reverse_lazy("enfermedades:enfermedad_list")
	success_message = "Enfermedad creada correctamente"

	def form_valid(self, form):
		form.instance.uc = self.request.user
		return super().form_valid(form)


class EnfermedadUpdateView(SuccessMessageMixin, SinPrivilegios, generic.UpdateView):
	"""Editar enfermedad."""

	permission_required = "enfermedades.change_enfermedad"
	model = Enfermedad
	form_class = EnfermedadForm
	template_name = "enfermedades/enfermedad_form.html"
	success_url = reverse_lazy("enfermedades:enfermedad_list")
	success_message = "Enfermedad actualizada correctamente"

	def form_valid(self, form):
		form.instance.um = self.request.user.id
		return super().form_valid(form)


class EnfermedadDeleteView(SuccessMessageMixin, SinPrivilegios, generic.DeleteView):
	"""Eliminar enfermedad."""

	permission_required = "enfermedades.delete_enfermedad"
	model = Enfermedad
	template_name = "enfermedades/enfermedad_confirm_delete.html"
	success_url = reverse_lazy("enfermedades:enfermedad_list")
	success_message = "Enfermedad eliminada correctamente"


@method_decorator(staff_member_required, name='dispatch')
class DashboardAlertasView(generic.ListView):
	"""
	Dashboard de alertas para administradores (SOOD-91).
	
	Vista exclusiva para personal staff que muestra:
	- Estadísticas generales de alertas
	- Listado de pacientes con alertas activas
	- Filtros por nivel de alerta
	- Gráficos y métricas del sistema
	"""
	
	model = Paciente
	template_name = "enfermedades/dashboard_alertas.html"
	context_object_name = "pacientes"
	paginate_by = 20
	
	def get_queryset(self):
		"""Filtra pacientes con alertas activas según filtros aplicados."""
		queryset = Paciente.objects.filter(estado=True).select_related()
		
		# Obtener pacientes con alertas activas
		pacientes_con_alertas = AlertaPaciente.objects.filter(
			es_activa=True
		).values_list('paciente_id', flat=True).distinct()
		
		queryset = queryset.filter(id__in=pacientes_con_alertas)
		
		# Filtro por nivel de alerta
		nivel_filtro = self.request.GET.get('nivel', '')
		if nivel_filtro in ['ROJO', 'AMARILLO', 'VERDE']:
			# Calculamos nivel para cada paciente y filtramos
			pacientes_filtrados = []
			for paciente in queryset:
				calc = CalculadorAlerta(paciente)
				if calc.calcular_nivel_alerta() == nivel_filtro:
					# Agregamos atributos calculados al objeto
					paciente.nivel_alerta = nivel_filtro
					paciente.semaforo_clase = self._get_semaforo_clase(nivel_filtro)
					paciente.semaforo_label = nivel_filtro
					paciente.factores_alerta = calc.obtener_factores_alerta()
					pacientes_filtrados.append(paciente)
			return pacientes_filtrados
		else:
			# Sin filtro, agregar datos calculados a todos
			for paciente in queryset:
				calc = CalculadorAlerta(paciente)
				nivel = calc.calcular_nivel_alerta()
				paciente.nivel_alerta = nivel
				paciente.semaforo_clase = self._get_semaforo_clase(nivel)
				paciente.semaforo_label = nivel
				paciente.factores_alerta = calc.obtener_factores_alerta()
		
		return queryset.order_by('-id')
	
	def get_context_data(self, **kwargs):
		"""Agrega estadísticas y datos adicionales al contexto."""
		context = super().get_context_data(**kwargs)
		
		# Estadísticas generales
		total_pacientes = Paciente.objects.filter(estado=True).count()
		alertas_activas = AlertaPaciente.objects.filter(
			es_activa=True
		).count()
		
		# Contar por nivel de alerta
		pacientes_activos = Paciente.objects.filter(estado=True)
		rojos = []
		amarillos = []
		verdes = []
		
		for paciente in pacientes_activos:
			calc = CalculadorAlerta(paciente)
			nivel = calc.calcular_nivel_alerta()
			if nivel == 'ROJO':
				rojos.append(paciente.id)
			elif nivel == 'AMARILLO':
				amarillos.append(paciente.id)
			elif nivel == 'VERDE':
				verdes.append(paciente.id)
		
		# Contar VIPs
		total_vips = Paciente.objects.filter(estado=True, es_vip=True).count()
		
		# Enfermedades más comunes en pacientes con alertas
		from enfermedades.models import EnfermedadPaciente
		enfermedades_comunes = EnfermedadPaciente.objects.filter(
			paciente__estado=True,
			paciente__id__in=[p.id for p in self.get_queryset()]
		).values(
			'enfermedad__nombre',
			'enfermedad__nivel_riesgo'
		).annotate(
			total=Count('id')
		).order_by('-total')[:10]
		
		context.update({
			'total_pacientes': total_pacientes,
			'total_alertas_activas': alertas_activas,
			'total_rojos': len(rojos),
			'total_amarillos': len(amarillos),
			'total_verdes': len(verdes),
			'total_vips': total_vips,
			'porcentaje_alertas': round((alertas_activas / total_pacientes * 100) if total_pacientes > 0 else 0, 1),
			'enfermedades_comunes': enfermedades_comunes,
			'nivel_filtro': self.request.GET.get('nivel', ''),
		})
		
		return context
	
	def _get_semaforo_clase(self, nivel):
		"""Retorna la clase CSS según el nivel de alerta."""
		clases = {
			'ROJO': 'semaforo-rojo',
			'AMARILLO': 'semaforo-amarillo',
			'VERDE': 'semaforo-verde'
		}
		return clases.get(nivel, 'semaforo-verde')

