"""
Vistas para el módulo de Pacientes (SOOD-46)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView
)
from django.views import View
from django.http import JsonResponse
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages

from .models import Paciente
from .forms import PacienteForm, PacienteBuscarForm
from cit.models import Cita
from enfermedades.forms import EnfermedadPacienteForm
from enfermedades.models import EnfermedadPaciente, AlertaPaciente
from enfermedades.utils import CalculadorAlerta
from core.services.tenants import get_clinica_from_request
from pacientes.services import pacientes_para_clinica, get_paciente_para_clinica


class PacienteListView(LoginRequiredMixin, ListView):
    """Lista de pacientes con búsqueda"""
    
    model = Paciente
    template_name = 'pacientes/paciente_list.html'
    context_object_name = 'pacientes'
    paginate_by = 20
    login_url = 'login'
    
    def get_queryset(self):
        """Filtrar pacientes según búsqueda y clínica activa (tenant-aware service)"""
        clinica = get_clinica_from_request(self.request)
        incluir_inactivos = self.request.GET.get('incluir_inactivos') == '1'
        if not clinica:
            return Paciente.objects.none()
        qs = pacientes_para_clinica(clinica, incluir_inactivos).order_by('apellidos', 'nombres')
        
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
        
        # Calcular niveles de alerta para cada paciente (SOOD-85)
        for paciente in context.get('pacientes', []):
            calculador = CalculadorAlerta(paciente)
            nivel = calculador.calcular_nivel_alerta()
            paciente.nivel_alerta = nivel
            paciente.semaforo_clase = {
                'ROJO': 'semaforo-rojo',
                'AMARILLO': 'semaforo-amarillo',
                'VERDE': 'semaforo-verde',
            }.get(nivel, 'semaforo-verde')
            paciente.semaforo_label = {
                'ROJO': 'Alerta Roja',
                'AMARILLO': 'Precaución',
                'VERDE': 'Sin alertas',
            }.get(nivel, 'Sin alertas')
        
        return context


class PacienteCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo paciente"""
    
    model = Paciente
    form_class = PacienteForm
    template_name = 'pacientes/paciente_form.html'
    success_url = reverse_lazy('pacientes:paciente-list')
    login_url = 'login'
    
    def form_valid(self, form):
        """Agregar usuario de auditoría y clínica activa"""
        paciente = form.save(commit=False)
        paciente.uc = self.request.user
        paciente.um = self.request.user.id
        
        # Asignar clínica activa desde sesión
        clinica_id = self.request.session.get('clinica_id')
        if clinica_id:
            paciente.clinica_id = clinica_id
        
        paciente.save()

        # Relación M2M con enfermedades, guardando auditoría en through
        enfermedades = form.cleaned_data.get('enfermedades')
        if enfermedades is not None:
            from enfermedades.models import EnfermedadPaciente
            EnfermedadPaciente.objects.filter(paciente=paciente).delete()
            EnfermedadPaciente.objects.bulk_create([
                EnfermedadPaciente(
                    paciente=paciente,
                    enfermedad=enf,
                    uc=self.request.user,
                    um=self.request.user.id,
                ) for enf in enfermedades
            ])

        messages.success(self.request, f'Paciente {paciente.get_nombre_completo()} creado exitosamente')
        self.object = paciente
        return super(CreateView, self).form_valid(form)
    
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
        """Actualizar usuario de auditoría y preservar la clínica"""
        paciente = form.save(commit=False)
        paciente.um = self.request.user.id
        # NO permitir cambiar la clínica - preservar la original
        paciente.clinica = self.get_object().clinica
        paciente.save()

        enfermedades = form.cleaned_data.get('enfermedades')
        if enfermedades is not None:
            from enfermedades.models import EnfermedadPaciente
            EnfermedadPaciente.objects.filter(paciente=paciente).delete()
            EnfermedadPaciente.objects.bulk_create([
                EnfermedadPaciente(
                    paciente=paciente,
                    enfermedad=enf,
                    uc=self.request.user,
                    um=self.request.user.id,
                ) for enf in enfermedades
            ])

        messages.success(self.request, f'Paciente {paciente.get_nombre_completo()} actualizado exitosamente')
        self.object = paciente
        return super(UpdateView, self).form_valid(form)
    
    def get_success_url(self):
        """Redirigir al listado de pacientes"""
        return reverse_lazy('pacientes:paciente-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar {self.object.get_nombre_completo()}'
        context['button_text'] = 'Actualizar Paciente'
        return context

    def get_queryset(self):
        """Filtrar por clínica del usuario y solo pacientes activos"""
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Paciente.objects.none()
        return Paciente.objects.filter(estado=True, clinica=clinica)


class PacienteDetailView(LoginRequiredMixin, DetailView):
    """Detalle de paciente con historial de citas"""
    
    model = Paciente
    template_name = 'pacientes/paciente_detail.html'
    context_object_name = 'paciente'
    login_url = 'login'

    def get_queryset(self):
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Paciente.objects.none()
        return Paciente.objects.filter(estado=True, clinica=clinica)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener citas del paciente ordenadas por fecha descendente
        # Usar select_related para cargar dentista, especialidad y usuario del dentista en una sola consulta
        context['citas'] = Cita.objects.filter(
            paciente=self.object
        ).select_related(
            'dentista',
            'dentista__usuario',
            'especialidad',
            'cubiculo'
        ).order_by('-fecha_hora')[:10]  # Últimas 10 citas
        
        # Estadísticas
        todas_citas = Cita.objects.filter(paciente=self.object)
        context['total_citas'] = todas_citas.count()
        context['citas_confirmadas'] = todas_citas.filter(estado='CON').count()
        context['citas_completadas'] = todas_citas.filter(estado='COM').count()
        
        # Enfermedades del paciente (SOOD-84)
        from enfermedades.models import EnfermedadPaciente
        
        enfermedades_activas = EnfermedadPaciente.objects.filter(
            paciente=self.object,
            estado_actual='ACTIVA'
        ).select_related('enfermedad', 'enfermedad__categoria').order_by(
            '-enfermedad__nivel_riesgo', 'enfermedad__nombre'
        )
        
        enfermedades_curadas = EnfermedadPaciente.objects.filter(
            paciente=self.object,
            estado_actual='CURADA'
        ).select_related('enfermedad', 'enfermedad__categoria').order_by(
            '-fm', 'enfermedad__nombre'
        )[:5]  # Últimas 5 curadas
        
        context['enfermedades_activas'] = enfermedades_activas
        context['enfermedades_curadas'] = enfermedades_curadas
        context['total_enfermedades'] = enfermedades_activas.count()
        context['enfermedades_criticas'] = enfermedades_activas.filter(enfermedad__nivel_riesgo='CRITICO').count()
        context['form_enfermedad'] = EnfermedadPacienteForm()

        # Semáforo de alertas (SOOD-86)
        calculador_alerta = CalculadorAlerta(self.object)
        nivel_alerta = calculador_alerta.calcular_nivel_alerta()
        context['nivel_alerta'] = nivel_alerta
        context['semaforo_clase'] = {
            'ROJO': 'semaforo-rojo',
            'AMARILLO': 'semaforo-amarillo',
            'VERDE': 'semaforo-verde',
        }.get(nivel_alerta, 'semaforo-verde')
        context['semaforo_label'] = {
            'ROJO': 'Alerta Roja',
            'AMARILLO': 'Precaución',
            'VERDE': 'Sin alertas',
        }.get(nivel_alerta, 'Sin alertas')
        context['factores_alerta'] = calculador_alerta.obtener_factores_alerta()
        context['resumen_alerta'] = calculador_alerta.get_resumen_estadistico()

        alertas_query = AlertaPaciente.objects.filter(paciente=self.object).order_by('-fc')
        context['alertas_activas'] = alertas_query.filter(es_activa=True)
        context['alertas_historial'] = alertas_query[:30]
        
        context['title'] = f'Detalle de {self.object.get_nombre_completo()}'
        # Garantizar disponibilidad de mensajes en contexto para tests
        context['messages'] = messages.get_messages(self.request)
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


class PacienteEnfermedadAddView(LoginRequiredMixin, View):
    """Crear relación EnfermedadPaciente vía AJAX modal."""
    login_url = 'login'

    def post(self, request, pk):
        clinica = get_clinica_from_request(request)
        paciente = get_object_or_404(Paciente, pk=pk, estado=True, clinica=clinica)
        form = EnfermedadPacienteForm(request.POST)
        if form.is_valid():
            try:
                ep = form.save(commit=False)
                ep.paciente = paciente
                ep.uc = request.user
                ep.um = request.user.id
                ep.save()
                return JsonResponse({'success': True})
            except IntegrityError:
                return JsonResponse({'success': False, 'errors': {'enfermedad': ['Ya existe esta enfermedad para el paciente.']}}, status=400)
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class PacienteEnfermedadDeleteView(LoginRequiredMixin, View):
    """Eliminar relación EnfermedadPaciente vía AJAX."""
    login_url = 'login'

    def post(self, request, pk, ep_id):
        clinica = get_clinica_from_request(request)
        paciente = get_object_or_404(Paciente, pk=pk, estado=True, clinica=clinica)
        ep = get_object_or_404(EnfermedadPaciente, pk=ep_id, paciente=paciente)
        ep.delete()
        return JsonResponse({'success': True})


class PacienteAlertasDetallesAJAXView(LoginRequiredMixin, View):
    """API AJAX para obtener detalles de alertas del paciente (SOOD-87)"""
    login_url = 'login'

    def get(self, request, pk):
        clinica = get_clinica_from_request(request)
        paciente = get_object_or_404(Paciente, pk=pk, estado=True, clinica=clinica)
        
        # Calcular nivel de alerta y factores
        calculador = CalculadorAlerta(paciente)
        nivel = calculador.calcular_nivel_alerta()
        factores = calculador.obtener_factores_alerta()
        
        # Obtener alertas activas
        alertas_activas = AlertaPaciente.objects.filter(
            paciente=paciente,
            es_activa=True
        ).order_by('-fc').values(
            'id', 'nivel', 'tipo', 'titulo', 'descripcion', 'fc', 'requiere_accion'
        )
        
        return JsonResponse({
            'success': True,
            'nivel_alerta': nivel,
            'label': {
                'ROJO': 'Alerta Roja',
                'AMARILLO': 'Precaución',
                'VERDE': 'Sin alertas',
            }.get(nivel, 'Sin alertas'),
            'factores': factores,
            'alertas_activas': list(alertas_activas),
            'paciente': {
                'id': paciente.id,
                'nombre': paciente.get_nombre_completo(),
                'cedula': paciente.cedula,
            }
        })

