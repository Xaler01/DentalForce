from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Cita, Dentista, Paciente, Especialidad, Cubiculo
from .forms import CitaForm, CitaCancelForm


# ============================================================================
# VISTAS CRUD DE CITAS
# ============================================================================

class CitaListView(LoginRequiredMixin, ListView):
    """
    Vista para listar todas las citas con filtros y búsqueda.
    """
    model = Cita
    template_name = 'cit/cita_list.html'
    context_object_name = 'citas'
    paginate_by = 25
    
    def get_queryset(self):
        """Optimizar consultas y aplicar filtros"""
        queryset = Cita.objects.select_related(
            'paciente',
            'dentista',
            'dentista__usuario',
            'especialidad',
            'cubiculo',
            'cubiculo__sucursal'
        ).all()
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por dentista
        dentista_id = self.request.GET.get('dentista')
        if dentista_id:
            queryset = queryset.filter(dentista_id=dentista_id)
        
        # Filtro por especialidad
        especialidad_id = self.request.GET.get('especialidad')
        if especialidad_id:
            queryset = queryset.filter(especialidad_id=especialidad_id)
        
        # Filtro por rango de fechas
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
                queryset = queryset.filter(fecha_hora__gte=fecha_desde_dt)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                # Incluir todo el día hasta
                fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(fecha_hora__lte=fecha_hasta_dt)
            except ValueError:
                pass
        
        # Búsqueda por paciente o dentista
        busqueda = self.request.GET.get('q')
        if busqueda:
            queryset = queryset.filter(
                Q(paciente__nombres__icontains=busqueda) |
                Q(paciente__apellidos__icontains=busqueda) |
                Q(paciente__cedula__icontains=busqueda) |
                Q(dentista__usuario__first_name__icontains=busqueda) |
                Q(dentista__usuario__last_name__icontains=busqueda)
            )
        
        return queryset.order_by('-fecha_hora')
    
    def get_context_data(self, **kwargs):
        """Agregar datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        
        # Lista de dentistas para el filtro
        context['dentistas'] = Dentista.objects.filter(estado=True).select_related('usuario')
        
        # Lista de especialidades para el filtro
        context['especialidades'] = Especialidad.objects.filter(estado=True)
        
        # Estados para el filtro
        context['estados'] = Cita.ESTADOS_CHOICES
        
        # Mantener los parámetros de búsqueda en el contexto
        context['estado_seleccionado'] = self.request.GET.get('estado', '')
        context['dentista_seleccionado'] = self.request.GET.get('dentista', '')
        context['especialidad_seleccionada'] = self.request.GET.get('especialidad', '')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['busqueda'] = self.request.GET.get('q', '')
        
        return context


class CitaDetailView(LoginRequiredMixin, DetailView):
    """
    Vista para mostrar los detalles de una cita.
    """
    model = Cita
    template_name = 'cit/cita_detail.html'
    context_object_name = 'cita'
    
    def get_queryset(self):
        """Optimizar consulta"""
        return Cita.objects.select_related(
            'paciente',
            'dentista',
            'dentista__usuario',
            'especialidad',
            'cubiculo',
            'cubiculo__sucursal'
        )


class CitaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva cita.
    """
    model = Cita
    form_class = CitaForm
    template_name = 'cit/cita_form.html'
    
    def get_initial(self):
        """Valores iniciales del formulario"""
        initial = super().get_initial()
        
        # Si viene un paciente_id por parámetro, pre-seleccionarlo
        paciente_id = self.request.GET.get('paciente_id')
        if paciente_id:
            try:
                initial['paciente'] = Paciente.objects.get(pk=paciente_id)
            except Paciente.DoesNotExist:
                pass
        
        # Si viene un dentista_id por parámetro, pre-seleccionarlo
        dentista_id = self.request.GET.get('dentista_id')
        if dentista_id:
            try:
                initial['dentista'] = Dentista.objects.get(pk=dentista_id)
            except Dentista.DoesNotExist:
                pass
        
        # Estado inicial: PENDIENTE
        initial['estado'] = Cita.ESTADO_PENDIENTE
        
        return initial
    
    def form_valid(self, form):
        """Procesar formulario válido"""
        # Establecer el usuario que crea la cita
        form.instance.uc = self.request.user
        form.instance.um = self.request.user.id
        
        # Guardar la cita
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Cita creada exitosamente para {self.object.paciente} '
            f'el {self.object.fecha_hora.strftime("%d/%m/%Y a las %H:%M")}'
        )
        
        return response
    
    def get_success_url(self):
        """Redireccionar al detalle de la cita creada"""
        return reverse('cit:cita-detail', kwargs={'pk': self.object.pk})


class CitaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar una cita existente.
    """
    model = Cita
    form_class = CitaForm
    template_name = 'cit/cita_form.html'
    
    def get_queryset(self):
        """Optimizar consulta"""
        return Cita.objects.select_related(
            'paciente',
            'dentista',
            'especialidad',
            'cubiculo'
        )
    
    def form_valid(self, form):
        """Procesar formulario válido"""
        # Establecer el usuario que modifica
        form.instance.um = self.request.user.id
        
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            f'Cita actualizada exitosamente'
        )
        
        return response
    
    def get_success_url(self):
        """Redireccionar al detalle de la cita"""
        return reverse('cit:cita-detail', kwargs={'pk': self.object.pk})


class CitaCancelView(LoginRequiredMixin, UpdateView):
    """
    Vista para cancelar una cita (no se elimina, solo se cambia el estado).
    """
    model = Cita
    form_class = CitaCancelForm
    template_name = 'cit/cita_confirm_cancel.html'
    
    def get_queryset(self):
        """Solo permitir cancelar citas que estén en estado PENDIENTE o CONFIRMADA"""
        return Cita.objects.filter(
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]
        ).select_related('paciente', 'dentista')
    
    def form_valid(self, form):
        """Cambiar estado a CANCELADA"""
        # Cambiar el estado a CANCELADA
        form.instance.estado = Cita.ESTADO_CANCELADA
        form.instance.usuario_modificacion = self.request.user
        
        response = super().form_valid(form)
        
        messages.warning(
            self.request,
            f'Cita cancelada. El paciente {self.object.paciente} ha sido notificado.'
        )
        
        return response
    
    def get_success_url(self):
        """Redireccionar a la lista de citas"""
        return reverse('cit:cita-list')


# ============================================================================
# VISTAS PARA CAMBIO DE ESTADO
# ============================================================================

@login_required
def confirmar_cita(request, pk):
    """Cambiar el estado de una cita a CONFIRMADA"""
    cita = get_object_or_404(Cita, pk=pk)
    
    if cita.estado != Cita.ESTADO_PENDIENTE:
        messages.error(request, 'Solo se pueden confirmar citas en estado PENDIENTE')
        return redirect('cit:cita-detail', pk=pk)
    
    cita.estado = Cita.ESTADO_CONFIRMADA
    cita.usuario_modificacion = request.user
    cita.save()
    
    messages.success(request, f'Cita confirmada exitosamente')
    return redirect('cit:cita-detail', pk=pk)


@login_required
def iniciar_atencion_cita(request, pk):
    """Cambiar el estado de una cita a EN_ATENCION"""
    cita = get_object_or_404(Cita, pk=pk)
    
    if cita.estado not in [Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]:
        messages.error(request, 'Solo se pueden iniciar citas en estado PENDIENTE o CONFIRMADA')
        return redirect('cit:cita-detail', pk=pk)
    
    cita.estado = Cita.ESTADO_EN_ATENCION
    cita.usuario_modificacion = request.user
    cita.save()
    
    messages.info(request, f'Atención iniciada')
    return redirect('cit:cita-detail', pk=pk)


@login_required
def completar_cita(request, pk):
    """Cambiar el estado de una cita a COMPLETADA"""
    cita = get_object_or_404(Cita, pk=pk)
    
    if cita.estado != Cita.ESTADO_EN_ATENCION:
        messages.error(request, 'Solo se pueden completar citas en estado EN_ATENCION')
        return redirect('cit:cita-detail', pk=pk)
    
    cita.estado = Cita.ESTADO_COMPLETADA
    cita.usuario_modificacion = request.user
    cita.save()
    
    messages.success(request, f'Cita completada exitosamente')
    return redirect('cit:cita-detail', pk=pk)


@login_required
def marcar_no_asistio(request, pk):
    """Marcar una cita como NO_ASISTIO"""
    cita = get_object_or_404(Cita, pk=pk)
    
    if cita.estado not in [Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]:
        messages.error(request, 'Solo se pueden marcar como no asistió citas PENDIENTE o CONFIRMADA')
        return redirect('cit:cita-detail', pk=pk)
    
    cita.estado = Cita.ESTADO_NO_ASISTIO
    cita.usuario_modificacion = request.user
    cita.save()
    
    messages.warning(request, f'Cita marcada como NO ASISTIÓ')
    return redirect('cit:cita-detail', pk=pk)


# ============================================================================
# ENDPOINTS AJAX
# ============================================================================

@login_required
def check_dentista_disponibilidad(request):
    """
    Verificar disponibilidad de un dentista en una fecha/hora específica.
    Retorna JSON con disponibilidad y mensajes.
    """
    dentista_id = request.GET.get('dentista_id')
    fecha_hora_str = request.GET.get('fecha_hora')
    duracion = request.GET.get('duracion', 30)
    cita_id = request.GET.get('cita_id')  # Para ediciones
    
    if not dentista_id or not fecha_hora_str:
        return JsonResponse({
            'disponible': False,
            'mensaje': 'Parámetros incompletos'
        })
    
    try:
        dentista = Dentista.objects.get(pk=dentista_id)
        # Convertir string a datetime
        fecha_hora = datetime.fromisoformat(fecha_hora_str.replace('Z', '+00:00'))
        duracion = int(duracion)
        
        # Calcular fecha de fin
        fecha_fin = fecha_hora + timedelta(minutes=duracion)
        
        # Buscar citas que solapen
        citas_solapadas = Cita.objects.filter(
            dentista=dentista,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        )
        
        # Excluir la cita actual si es edición
        if cita_id:
            citas_solapadas = citas_solapadas.exclude(pk=cita_id)
        
        # Verificar solapamiento
        for cita in citas_solapadas:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                return JsonResponse({
                    'disponible': False,
                    'mensaje': f'El Dr./Dra. {dentista} ya tiene una cita en este horario '
                              f'({cita.fecha_hora.strftime("%H:%M")} - {cita_fin.strftime("%H:%M")})',
                    'citas_solapadas': [{
                        'id': cita.id,
                        'paciente': str(cita.paciente),
                        'fecha_hora': cita.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                        'duracion': cita.duracion
                    }]
                })
        
        return JsonResponse({
            'disponible': True,
            'mensaje': f'Dr./Dra. {dentista} disponible en este horario'
        })
        
    except (Dentista.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'disponible': False,
            'mensaje': f'Error: {str(e)}'
        })


@login_required
def check_cubiculo_disponibilidad(request):
    """
    Verificar disponibilidad de un cubículo en una fecha/hora específica.
    Retorna JSON con disponibilidad y mensajes.
    """
    cubiculo_id = request.GET.get('cubiculo_id')
    fecha_hora_str = request.GET.get('fecha_hora')
    duracion = request.GET.get('duracion', 30)
    cita_id = request.GET.get('cita_id')  # Para ediciones
    
    if not cubiculo_id or not fecha_hora_str:
        return JsonResponse({
            'disponible': False,
            'mensaje': 'Parámetros incompletos'
        })
    
    try:
        cubiculo = Cubiculo.objects.get(pk=cubiculo_id)
        # Convertir string a datetime
        fecha_hora = datetime.fromisoformat(fecha_hora_str.replace('Z', '+00:00'))
        duracion = int(duracion)
        
        # Calcular fecha de fin
        fecha_fin = fecha_hora + timedelta(minutes=duracion)
        
        # Buscar citas que solapen
        citas_solapadas = Cita.objects.filter(
            cubiculo=cubiculo,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        )
        
        # Excluir la cita actual si es edición
        if cita_id:
            citas_solapadas = citas_solapadas.exclude(pk=cita_id)
        
        # Verificar solapamiento
        for cita in citas_solapadas:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                return JsonResponse({
                    'disponible': False,
                    'mensaje': f'El cubículo {cubiculo} ya está ocupado en este horario '
                              f'({cita.fecha_hora.strftime("%H:%M")} - {cita_fin.strftime("%H:%M")})',
                    'citas_solapadas': [{
                        'id': cita.id,
                        'dentista': str(cita.dentista),
                        'paciente': str(cita.paciente),
                        'fecha_hora': cita.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                        'duracion': cita.duracion
                    }]
                })
        
        return JsonResponse({
            'disponible': True,
            'mensaje': f'Cubículo {cubiculo} disponible en este horario'
        })
        
    except (Cubiculo.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'disponible': False,
            'mensaje': f'Error: {str(e)}'
        })


@login_required
def get_dentista_especialidades(request, dentista_id):
    """
    Obtener las especialidades de un dentista.
    Retorna JSON con la lista de especialidades.
    """
    try:
        dentista = Dentista.objects.prefetch_related('especialidades').get(pk=dentista_id)
        
        especialidades = [{
            'id': esp.id,
            'nombre': esp.nombre,
            'color': esp.color_calendario,
            'duracion_default': esp.duracion_default
        } for esp in dentista.especialidades.filter(estado=True)]
        
        return JsonResponse({
            'success': True,
            'especialidades': especialidades,
            'dentista': str(dentista)
        })
        
    except Dentista.DoesNotExist:
        return JsonResponse({
            'success': False,
            'mensaje': 'Dentista no encontrado'
        })


@login_required
def get_especialidad_dentistas(request, especialidad_id):
    """
    Obtener los dentistas que practican una especialidad.
    Retorna JSON con la lista de dentistas.
    """
    try:
        especialidad = Especialidad.objects.prefetch_related('dentistas').get(pk=especialidad_id)
        
        dentistas = [{
            'id': dentista.id,
            'nombre': str(dentista),
            'usuario_nombre': dentista.usuario.get_full_name() or dentista.usuario.username
        } for dentista in especialidad.dentistas.filter(estado=True)]
        
        return JsonResponse({
            'success': True,
            'dentistas': dentistas,
            'especialidad': especialidad.nombre
        })
        
    except Especialidad.DoesNotExist:
        return JsonResponse({
            'success': False,
            'mensaje': 'Especialidad no encontrada'
        })


# ============================================================================
# VISTAS DE CALENDARIO
# ============================================================================

class CalendarioCitasView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar el calendario de citas con FullCalendar.
    """
    model = Cita
    template_name = 'cit/calendario_citas.html'
    context_object_name = 'citas'
    
    def get_context_data(self, **kwargs):
        """Agregar datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        
        # Lista de dentistas para filtros
        context['dentistas'] = Dentista.objects.filter(estado=True).select_related('usuario')
        
        # Lista de especialidades para filtros
        context['especialidades'] = Especialidad.objects.filter(estado=True)
        
        # Estados para filtros
        context['estados'] = Cita.ESTADOS_CHOICES
        
        return context


@login_required
def citas_json(request):
    """
    Endpoint JSON para FullCalendar.
    Retorna las citas en formato de eventos de FullCalendar.
    """
    # Obtener parámetros de fecha de FullCalendar
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Filtros opcionales
    dentista_id = request.GET.get('dentista_id')
    especialidad_id = request.GET.get('especialidad_id')
    estado = request.GET.get('estado')
    
    # Consulta base con optimización
    queryset = Cita.objects.select_related(
        'paciente',
        'dentista',
        'dentista__usuario',
        'especialidad',
        'cubiculo'
    ).all()
    
    # Filtrar por rango de fechas si se proporciona
    if start and end:
        try:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            queryset = queryset.filter(
                fecha_hora__gte=start_date,
                fecha_hora__lte=end_date
            )
        except ValueError:
            pass
    
    # Aplicar filtros adicionales
    if dentista_id:
        queryset = queryset.filter(dentista_id=dentista_id)
    
    if especialidad_id:
        queryset = queryset.filter(especialidad_id=especialidad_id)
    
    if estado:
        queryset = queryset.filter(estado=estado)
    
    # Construir eventos para FullCalendar
    eventos = []
    for cita in queryset:
        # Calcular fecha de fin
        fecha_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
        
        # Determinar color según estado
        color_map = {
            Cita.ESTADO_PENDIENTE: '#ffc107',      # warning - amarillo
            Cita.ESTADO_CONFIRMADA: '#17a2b8',     # info - azul
            Cita.ESTADO_EN_ATENCION: '#007bff',    # primary - azul oscuro
            Cita.ESTADO_COMPLETADA: '#28a745',     # success - verde
            Cita.ESTADO_CANCELADA: '#6c757d',      # secondary - gris
            Cita.ESTADO_NO_ASISTIO: '#dc3545',     # danger - rojo
        }
        
        evento = {
            'id': cita.id,
            'title': f"{cita.paciente.nombres} {cita.paciente.apellidos}",
            'start': cita.fecha_hora.isoformat(),
            'end': fecha_fin.isoformat(),
            'backgroundColor': color_map.get(cita.estado, '#6c757d'),
            'borderColor': color_map.get(cita.estado, '#6c757d'),
            'textColor': '#ffffff',
            'extendedProps': {
                'paciente': str(cita.paciente),
                'paciente_cedula': cita.paciente.cedula,
                'dentista': str(cita.dentista),
                'especialidad': cita.especialidad.nombre,
                'especialidad_color': cita.especialidad.color_calendario,
                'cubiculo': cita.cubiculo.nombre,
                'estado': cita.get_estado_display(),
                'estado_codigo': cita.estado,
                'duracion': cita.duracion,
                'duracion_display': cita.get_duracion_display_horas(),
                'observaciones': cita.observaciones or '',
            }
        }
        eventos.append(evento)
    
    return JsonResponse(eventos, safe=False)
