from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse

from .models import Clinica


class ClinicaSelectView(LoginRequiredMixin, View):
    """Selector de clínica independiente del módulo de citas."""
    template_name = 'clinicas/clinica_select.html'

    def get(self, request):
        # Admin ve todas las clínicas; usuarios regulares solo activas
        if request.user.is_staff and request.user.is_superuser:
            clinicas = list(Clinica.objects.all().order_by('nombre'))
        else:
            clinicas = list(Clinica.objects.filter(estado=True).order_by('nombre'))

        context = {
            'clinicas': clinicas,
            'clinica_actual_id': request.session.get('clinica_id'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        clinica_id = request.POST.get('clinica_id')
        if not clinica_id:
            messages.error(request, 'Debe seleccionar una clínica.')
            return redirect('clinicas:seleccionar')

        try:
            if request.user.is_staff and request.user.is_superuser:
                clinica = Clinica.objects.get(pk=clinica_id)
            else:
                clinica = Clinica.objects.get(pk=clinica_id, estado=True)
        except Clinica.DoesNotExist:
            messages.error(request, 'La clínica seleccionada no existe o está inactiva.')
            return redirect('clinicas:seleccionar')

        request.session['clinica_id'] = clinica.id
        messages.success(request, f'Clínica "{clinica.nombre}" seleccionada.')
        next_url = request.GET.get('next', reverse('bases:home'))
        return redirect(next_url)
