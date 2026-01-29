from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView

from .models import Personal, RegistroHorasPersonal
from .forms import PersonalForm, RegistroHorasPersonalForm


class PersonalListView(LoginRequiredMixin, ListView):
	model = Personal
	template_name = 'personal/personal_list.html'
	context_object_name = 'personal_list'


class PersonalCreateView(LoginRequiredMixin, CreateView):
	model = Personal
	form_class = PersonalForm
	template_name = 'personal/personal_form.html'
	success_url = '/personal/'

	def form_valid(self, form):
		form.instance.uc = self.request.user
		response = super().form_valid(form)
		messages.success(self.request, '✅ Personal creado correctamente')
		return response


class PersonalUpdateView(LoginRequiredMixin, UpdateView):
	model = Personal
	form_class = PersonalForm
	template_name = 'personal/personal_form.html'
	success_url = '/personal/'

	def form_valid(self, form):
		form.instance.um = self.request.user.id
		response = super().form_valid(form)
		messages.success(self.request, '✅ Personal actualizado correctamente')
		return response


class PersonalHorasExtraCreateView(LoginRequiredMixin, CreateView):
	model = RegistroHorasPersonal
	form_class = RegistroHorasPersonalForm
	template_name = 'personal/horas_extra_form.html'
	success_url = '/personal/horas-extra/'

	def form_valid(self, form):
		try:
			personal = self.request.user.personal_profile
		except Personal.DoesNotExist:
			messages.error(self.request, '❌ No tiene perfil de Personal asociado')
			return redirect('personal:personal-list')

		form.instance.personal = personal
		form.instance.uc = self.request.user
		response = super().form_valid(form)
		messages.success(self.request, '✅ Horas extra registradas correctamente')
		return response


class PersonalHorasExtraListView(LoginRequiredMixin, ListView):
	model = RegistroHorasPersonal
	template_name = 'personal/horas_extra_list.html'
	context_object_name = 'horas_list'

	def get_queryset(self):
		return RegistroHorasPersonal.objects.select_related('personal', 'personal__usuario').order_by('-fecha')


class PersonalHorasExtraAprobarView(LoginRequiredMixin, UpdateView):
	model = RegistroHorasPersonal
	fields = ['estado', 'observaciones']
	template_name = 'personal/horas_extra_aprobar.html'
	success_url = '/personal/horas-extra/'

	def form_valid(self, form):
		if form.instance.estado == 'APROBADO':
			form.instance.aprobado_por = self.request.user
			form.instance.aprobado_en = timezone.now()
		response = super().form_valid(form)
		messages.success(self.request, '✅ Registro actualizado')
		return response
