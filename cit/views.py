from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

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


@login_required
@require_http_methods(["PATCH"])
def mover_cita(request, pk):
    """
    Endpoint PATCH para reprogramar una cita (drag & drop).
    Actualiza fecha_hora y/o duración con validaciones de disponibilidad.
    """
    try:
        cita = Cita.objects.select_related(
            'paciente', 'dentista', 'especialidad', 'cubiculo'
        ).get(pk=pk)
    except Cita.DoesNotExist:
        return JsonResponse({
            'success': False,
            'mensaje': 'Cita no encontrada'
        }, status=404)
    
    # Solo permitir mover citas no canceladas ni completadas
    if cita.estado in [Cita.ESTADO_CANCELADA, Cita.ESTADO_COMPLETADA, Cita.ESTADO_NO_ASISTIO]:
        return JsonResponse({
            'success': False,
            'mensaje': f'No se puede reprogramar una cita en estado {cita.get_estado_display()}'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        nueva_fecha_hora_str = data.get('fecha_hora')
        nueva_duracion = data.get('duracion')
        
        if not nueva_fecha_hora_str:
            return JsonResponse({
                'success': False,
                'mensaje': 'Debe proporcionar la nueva fecha y hora'
            }, status=400)
        
        # Parsear fecha
        from datetime import datetime
        nueva_fecha_hora = datetime.fromisoformat(nueva_fecha_hora_str.replace('Z', '+00:00'))
        
        # Usar duración actual si no se proporciona
        if nueva_duracion is None:
            nueva_duracion = cita.duracion
        else:
            nueva_duracion = int(nueva_duracion)
        
        # ====================================================================
        # VALIDACIONES
        # ====================================================================
        
        # 1. Validar que no sea en el pasado
        from django.utils import timezone
        if nueva_fecha_hora < timezone.now():
            return JsonResponse({
                'success': False,
                'mensaje': 'No se puede reprogramar una cita en el pasado'
            }, status=400)
        
        # 2. Validar duración
        if nueva_duracion < 15:
            return JsonResponse({
                'success': False,
                'mensaje': 'La duración mínima es 15 minutos'
            }, status=400)
        
        if nueva_duracion > 240:
            return JsonResponse({
                'success': False,
                'mensaje': 'La duración máxima es 240 minutos (4 horas)'
            }, status=400)
        
        # 3. Validar horario laboral (08:00 - 20:00)
        hora_inicio = nueva_fecha_hora.time()
        from datetime import time, timedelta
        
        if hora_inicio < time(8, 0):
            return JsonResponse({
                'success': False,
                'mensaje': 'El horario laboral inicia a las 08:00'
            }, status=400)
        
        fecha_fin = nueva_fecha_hora + timedelta(minutes=nueva_duracion)
        if fecha_fin.time() > time(20, 0):
            return JsonResponse({
                'success': False,
                'mensaje': f'La cita terminaría a las {fecha_fin.strftime("%H:%M")}, después del cierre (20:00)'
            }, status=400)
        
        # 4. Validar disponibilidad del dentista
        citas_solapadas = Cita.objects.filter(
            dentista=cita.dentista,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=cita.pk)
        
        for otra_cita in citas_solapadas:
            otra_fin = otra_cita.fecha_hora + timedelta(minutes=otra_cita.duracion)
            if otra_cita.fecha_hora < fecha_fin and otra_fin > nueva_fecha_hora:
                return JsonResponse({
                    'success': False,
                    'mensaje': f'El Dr./Dra. {cita.dentista} ya tiene una cita en ese horario ({otra_cita.fecha_hora.strftime("%H:%M")} - {otra_fin.strftime("%H:%M")})'
                }, status=400)
        
        # 5. Validar disponibilidad del cubículo
        citas_cubiculo = Cita.objects.filter(
            cubiculo=cita.cubiculo,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=cita.pk)
        
        for otra_cita in citas_cubiculo:
            otra_fin = otra_cita.fecha_hora + timedelta(minutes=otra_cita.duracion)
            if otra_cita.fecha_hora < fecha_fin and otra_fin > nueva_fecha_hora:
                return JsonResponse({
                    'success': False,
                    'mensaje': f'El cubículo {cita.cubiculo} ya está ocupado en ese horario'
                }, status=400)
        
        # ====================================================================
        # ACTUALIZAR CITA
        # ====================================================================
        cita.fecha_hora = nueva_fecha_hora
        cita.duracion = nueva_duracion
        cita.um = request.user.id
        cita.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Cita reprogramada exitosamente',
            'cita': {
                'id': cita.id,
                'fecha_hora': cita.fecha_hora.isoformat(),
                'duracion': cita.duracion,
                'paciente': str(cita.paciente),
                'dentista': str(cita.dentista),
                'estado': cita.get_estado_display()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'mensaje': 'Datos JSON inválidos'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'mensaje': f'Error en los datos: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'mensaje': f'Error inesperado: {str(e)}'
        }, status=500)


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
        from .models import ConfiguracionClinica
        import json
        
        context = super().get_context_data(**kwargs)
        
        # Lista de dentistas para filtros
        context['dentistas'] = Dentista.objects.filter(estado=True).select_related('usuario')
        
        # Lista de especialidades para filtros
        context['especialidades'] = Especialidad.objects.filter(estado=True)
        
        # Estados para filtros
        context['estados'] = Cita.ESTADOS_CHOICES
        
        # Obtener configuración de la clínica
        config = ConfiguracionClinica.objects.filter(estado=True).first()
        
        if config:
            # Convertir configuración a formato para JavaScript
            config_data = {
                'horario_inicio': config.horario_inicio.strftime('%H:%M'),
                'horario_fin': config.horario_fin.strftime('%H:%M'),
                'duracion_slot': config.duracion_slot,
                'dias_atencion': config.get_dias_atencion(),
                'sabado_hora_inicio': config.sabado_hora_inicio.strftime('%H:%M') if config.sabado_hora_inicio else None,
                'sabado_hora_fin': config.sabado_hora_fin.strftime('%H:%M') if config.sabado_hora_fin else None,
                'permitir_mismo_dia': config.permitir_citas_mismo_dia,
                'horas_anticipacion': config.horas_anticipacion_minima,
            }
            context['configuracion'] = config
            context['configuracion_json'] = json.dumps(config_data)
        else:
            # Configuración por defecto
            config_data = {
                'horario_inicio': '08:30',
                'horario_fin': '18:00',
                'duracion_slot': 30,
                'dias_atencion': [0, 1, 2, 3, 4, 5],  # Lunes a sábado
                'sabado_hora_inicio': '08:30',
                'sabado_hora_fin': '12:00',
                'permitir_mismo_dia': True,
                'horas_anticipacion': 0,
            }
            context['configuracion'] = None
            context['configuracion_json'] = json.dumps(config_data)
        
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
