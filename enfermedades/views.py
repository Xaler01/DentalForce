from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.views import generic

from bases.views import SinPrivilegios
from .models import CategoriaEnfermedad, Enfermedad
from .forms import CategoriaEnfermedadForm, EnfermedadForm


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
