"""
Vistas para el módulo de Pacientes (SOOD-46)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView
)
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages

from .models import Paciente
from .forms import PacienteForm, PacienteBuscarForm
from cit.models import Cita


class PacienteListView(LoginRequiredMixin, ListView):
    """Lista de pacientes con búsqueda"""
    
    model = Paciente
    template_name = 'pacientes/paciente_list.html'
    context_object_name = 'pacientes'
    paginate_by = 20
    login_url = 'login'
    
    def get_queryset(self):
        """Filtrar pacientes según búsqueda"""
        incluir_inactivos = self.request.GET.get('incluir_inactivos') == '1'
        qs = Paciente.objects.all().order_by('apellidos', 'nombres') if incluir_inactivos else Paciente.objects.filter(estado=True).order_by('apellidos', 'nombres')
        
        form = PacienteBuscarForm(self.request.GET)
        if form.is_valid():
            buscar = form.cleaned_data.get('buscar', '').strip()
            genero = form.cleaned_data.get('genero', '').strip()
            tipo_sangre = form.cleaned_data.get('tipo_sangre', '').strip()
            
            if buscar:
                qs = qs.filter(
                    Q(nombres__icontains=buscar) |
                    Q(apellidos__icontains=buscar) |
                    Q(cedula__icontains=buscar) |
                    Q(telefono__icontains=buscar)
                )
            
            if genero:
                qs = qs.filter(genero=genero)
            
            if tipo_sangre:
                qs = qs.filter(tipo_sangre=tipo_sangre)
        
        return qs
    
    def get_context_data(self, **kwargs):
        """Agregar formulario de búsqueda al contexto"""
        context = super().get_context_data(**kwargs)
        context['form'] = PacienteBuscarForm(self.request.GET)
        context['title'] = 'Lista de Pacientes'
        context['incluir_inactivos'] = self.request.GET.get('incluir_inactivos') == '1'
        return context


class PacienteCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo paciente"""
    
    model = Paciente
    form_class = PacienteForm
    template_name = 'pacientes/paciente_form.html'
    success_url = reverse_lazy('pacientes:paciente-list')
    login_url = 'login'
    
    def form_valid(self, form):
        """Agregar usuario de auditoría"""
        form.instance.uc = self.request.user
        form.instance.um = self.request.user.id
        messages.success(self.request, f'Paciente {form.instance.get_nombre_completo()} creado exitosamente')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Paciente'
        context['button_text'] = 'Crear Paciente'
        return context


class PacienteUpdateView(LoginRequiredMixin, UpdateView):
    """Editar paciente existente"""
    
    model = Paciente
    form_class = PacienteForm
    template_name = 'pacientes/paciente_form.html'
    login_url = 'login'
    
    def form_valid(self, form):
        """Actualizar usuario de auditoría"""
        form.instance.um = self.request.user.id
        messages.success(self.request, f'Paciente {form.instance.get_nombre_completo()} actualizado exitosamente')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirigir al detalle del paciente"""
        return reverse_lazy('pacientes:paciente-detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar {self.object.get_nombre_completo()}'
        context['button_text'] = 'Actualizar Paciente'
        return context

    def get_queryset(self):
        """Operar solo sobre pacientes activos"""
        return Paciente.objects.filter(estado=True)


class PacienteDetailView(LoginRequiredMixin, DetailView):
    """Detalle de paciente con historial de citas"""
    
    model = Paciente
    template_name = 'pacientes/paciente_detail.html'
    context_object_name = 'paciente'
    login_url = 'login'

    def get_queryset(self):
        return Paciente.objects.filter(estado=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener citas del paciente ordenadas por fecha descendente
        context['citas'] = Cita.objects.filter(
            paciente=self.object
        ).order_by('-fecha_hora')[:10]  # Últimas 10 citas
        
        # Estadísticas
        todas_citas = Cita.objects.filter(paciente=self.object)
        context['total_citas'] = todas_citas.count()
        context['citas_confirmadas'] = todas_citas.filter(estado='CON').count()
        context['citas_completadas'] = todas_citas.filter(estado='COM').count()
        
        context['title'] = f'Detalle de {self.object.get_nombre_completo()}'
        return context


class PacienteDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar (soft delete) paciente"""
    
    model = Paciente
    template_name = 'pacientes/paciente_confirm_delete.html'
    success_url = reverse_lazy('pacientes:paciente-list')
    login_url = 'login'

    def get_queryset(self):
        return Paciente.objects.filter(estado=True)
    
    def delete(self, request, *args, **kwargs):
        """Realizar soft delete (desactivar)"""
        self.object = self.get_object()
        nombre = self.object.get_nombre_completo()

        # Soft delete garantizado vía update (evita delete accidental)
        Paciente.objects.filter(pk=self.object.pk).update(
            estado=False,
            um=request.user.id
        )

        messages.success(request, f'Paciente {nombre} desactivado exitosamente')
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        """Evitar llamada al delete de la superclase que elimina el registro"""
        return self.delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar {self.object.get_nombre_completo()}'
        # Advertencia si tiene citas activas (confirmadas o pendientes)
        citas_activas = Cita.objects.filter(
            paciente=self.object,
            estado__in=['CON']  # Confirmadas
        ).count()
        if citas_activas > 0:
            context['warning'] = f'Este paciente tiene {citas_activas} cita(s) activa(s)'
        return context


class PacienteReactivateView(LoginRequiredMixin, View):
    """Reactivar un paciente desactivado"""
    login_url = 'login'

    def post(self, request, pk):
        paciente = get_object_or_404(Paciente, pk=pk, estado=False)
        paciente.estado = True
        paciente.um = request.user.id
        paciente.save()
        messages.success(request, f'Paciente {paciente.get_nombre_completo()} reactivado exitosamente')
        return redirect(reverse_lazy('pacientes:paciente-list') + '?incluir_inactivos=1')
