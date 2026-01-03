from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.views import generic

from bases.views import SinPrivilegios
from .models import CategoriaEnfermedad
from .forms import CategoriaEnfermedadForm


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
