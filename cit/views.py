from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction
from datetime import datetime, timedelta
import json

from .models import Cita, Dentista, Paciente, Especialidad, Cubiculo, Clinica, Sucursal
from .forms import CitaForm, CitaCancelForm, EspecialidadForm, SucursalForm
from .services import citas_para_clinica, get_cita_para_clinica
from core.services.tenants import get_clinica_from_request


# ============================================================================
# VISTAS CRUD DE CITAS
# ============================================================================

class CitaListView(LoginRequiredMixin, ListView):
    """
    Vista para listar todas las citas con filtros y búsqueda.
    Tenant-aware: filtra por clínica activa usando servicios.
    """
    model = Cita
    template_name = 'cit/cita_list.html'
    context_object_name = 'citas'
    paginate_by = 25
    
    def get_queryset(self):
        """Filtrar citas por clínica activa usando servicio tenant-aware"""
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Cita.objects.none()
        
        # Obtener queryset base filtrado por clínica
        queryset = citas_para_clinica(clinica)
        
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
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Agregar datos adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        clinica = get_clinica_from_request(self.request)
        
        # Lista de dentistas para el filtro (solo los de la clínica activa)
        if clinica:
            # Obtener dentistas que tienen sucursales en la clínica
            context['dentistas'] = Dentista.objects.filter(
                estado=True,
                sucursal_principal__clinica=clinica
            ).select_related('usuario').distinct()
        else:
            context['dentistas'] = Dentista.objects.none()
        
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
    Tenant-aware: valida que la cita pertenezca a la clínica activa.
    """
    model = Cita
    template_name = 'cit/cita_detail.html'
    context_object_name = 'cita'
    
    def get_object(self):
        """Obtener cita con validación de clínica activa"""
        clinica = get_clinica_from_request(self.request)
        pk = self.kwargs.get('pk')
        return get_cita_para_clinica(pk, clinica)
    
    def get_queryset(self):
        """Retornar queryset base (no se usa en detail view)"""
        return Cita.objects.all()
    
    def get_context_data(self, **kwargs):
        """Agregar usuario de modificación al contexto"""
        context = super().get_context_data(**kwargs)
        cita = self.get_object()
        
        if cita and cita.um:
            from django.contrib.auth.models import User
            try:
                usuario_modificacion = User.objects.get(id=cita.um)
                context['usuario_modificacion'] = usuario_modificacion
            except User.DoesNotExist:
                context['usuario_modificacion'] = None
        else:
            context['usuario_modificacion'] = None
        
        return context


class CitaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva cita.
    Tenant-aware: solo muestra pacientes y dentistas de la clínica activa.
    """
    model = Cita
    form_class = CitaForm
    template_name = 'cit/cita_form.html'
    
    def get_form_kwargs(self):
        """Pasar clínica activa al formulario"""
        kwargs = super().get_form_kwargs()
        clinica = get_clinica_from_request(self.request)
        kwargs['clinica'] = clinica
        return kwargs
    
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

        # Preseleccionar fecha/hora si viene desde el calendario
        start_param = self.request.GET.get('start')
        if start_param:
            parsed_start = parse_datetime(start_param)
            if parsed_start:
                if timezone.is_naive(parsed_start):
                    parsed_start = timezone.make_aware(parsed_start, timezone.get_current_timezone())
                # Guardar la fecha en zona local para que el widget datetime-local muestre la hora correcta
                initial['fecha_hora'] = timezone.localtime(parsed_start)

        # Preseleccionar duración si viene desde el calendario
        duration_param = self.request.GET.get('duration')
        if duration_param:
            try:
                duration_int = int(duration_param)
                # Obtener las opciones permitidas del widget del formulario
                duracion_widget = self.form_class().fields['duracion'].widget
                allowed_durations = [choice[0] for choice in duracion_widget.choices]
                if duration_int in allowed_durations:
                    initial['duracion'] = duration_int
            except (ValueError, TypeError, AttributeError):
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
    Tenant-aware: solo permite editar citas de la clínica activa.
    """
    model = Cita
    form_class = CitaForm
    template_name = 'cit/cita_form.html'
    
    def get_form_kwargs(self):
        """Pasar clínica activa al formulario"""
        kwargs = super().get_form_kwargs()
        clinica = get_clinica_from_request(self.request)
        kwargs['clinica'] = clinica
        return kwargs
    
    def get_queryset(self):
        """Filtrar por clínica activa y optimizar consulta"""
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Cita.objects.none()
        
        return Cita.objects.filter(
            paciente__clinica=clinica
        ).select_related(
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


from .forms import CitaForm, CitaCancelForm, EspecialidadForm, SucursalForm, CitaCancelSimpleForm


class CitaCancelView(LoginRequiredMixin, View):
    """
    Maneja GET y POST para cancelar una cita usando un formulario simple
    que solo valida el motivo de cancelación y evita ejecutar las
    validaciones completas del modelo.
    """
    template_name = 'cit/cita_confirm_cancel.html'

    def get_queryset(self):
        return Cita.objects.filter(
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]
        ).select_related('paciente', 'dentista', 'cubiculo', 'especialidad')

    def get(self, request, pk):
        cita = get_object_or_404(self.get_queryset(), pk=pk)
        form = CitaCancelSimpleForm(initial={'motivo_cancelacion': cita.motivo_cancelacion})
        return render(request, self.template_name, {'form': form, 'object': cita})

    def post(self, request, pk):
        cita = get_object_or_404(self.get_queryset(), pk=pk)
        form = CitaCancelSimpleForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'object': cita})

        # Actualizar la cita y guardar
        cita.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
        cita.estado = Cita.ESTADO_CANCELADA
        try:
            cita.usuario_modificacion = request.user
        except Exception:
            pass
        cita.save()

        messages.warning(request, f'Cita cancelada. El paciente {cita.paciente} ha sido notificado.')
        return redirect(reverse('cit:cita-list'))


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


@login_required
@require_http_methods(["POST"])
def cambiar_estado_cita_ajax(request, pk):
    """
    Endpoint AJAX para cambiar el estado de una cita.
    Retorna JSON con el nuevo estado.
    """
    try:
        cita = get_object_or_404(Cita, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        # Estados permitidos
        estados_validos = [
            Cita.ESTADO_PENDIENTE,
            Cita.ESTADO_CONFIRMADA,
            Cita.ESTADO_CANCELADA,
            Cita.ESTADO_EN_ATENCION,
            Cita.ESTADO_COMPLETADA,
            Cita.ESTADO_NO_ASISTIO,
        ]
        
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'mensaje': 'Estado no válido'
            }, status=400)
        
        # Validar transiciones de estado permitidas
        estado_actual = cita.estado
        
        # Citas canceladas no se pueden modificar
        if estado_actual == Cita.ESTADO_CANCELADA:
            return JsonResponse({
                'success': False,
                'mensaje': 'No se pueden modificar citas canceladas'
            }, status=400)
        
        # Citas completadas solo pueden pasar a canceladas
        if estado_actual == Cita.ESTADO_COMPLETADA:
            if nuevo_estado != Cita.ESTADO_CANCELADA:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Las citas completadas solo pueden ser canceladas'
                }, status=400)
        
        # Citas en atención pueden completarse, cancelarse o no asistir
        if estado_actual == Cita.ESTADO_EN_ATENCION:
            if nuevo_estado not in [Cita.ESTADO_COMPLETADA, Cita.ESTADO_CANCELADA, Cita.ESTADO_NO_ASISTIO]:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Estado de transición no permitido'
                }, status=400)
        
        # Pendiente/Confirmada pueden ir a cualquier lado
        
        # Actualizar la cita
        cita.estado = nuevo_estado
        cita.um = request.user.id
        cita.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Estado actualizado a {cita.get_estado_display()}',
            'nuevo_estado': nuevo_estado,
            'nuevo_estado_display': cita.get_estado_display(),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'mensaje': f'Error: {str(e)}'
        }, status=500)


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
                    'mensaje': f'El dentista Dr./Dra. {dentista} ya tiene una cita en este horario '
                              f'({cita.fecha_hora.strftime("%H:%M")} - {cita_fin.strftime("%H:%M")})',
                    'citas_solapadas': [{
                        'id': cita.id,
                        'paciente': str(cita.paciente),
                        'fecha_hora': cita.fecha_hora.strftime('%d/%m/%Y %H:%M'),
                        'duracion': cita.duracion
                    }]
                })
        # Si no se encontraron solapamientos, está disponible
        return JsonResponse({
            'disponible': True,
            'mensaje': f'Dentista {dentista} disponible en este horario'
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
                    'mensaje': f'El dentista Dr./Dra. {cita.dentista} ya tiene una cita en ese horario ({otra_cita.fecha_hora.strftime("%H:%M")} - {otra_fin.strftime("%H:%M")})'
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
    
    # Obtener clínica activa desde sesión
    clinica_id = request.session.get('clinica_id')
    
    # Consulta base con optimización y filtro de clínica
    if clinica_id:
        queryset = Cita.objects.para_clinica(clinica_id).select_related(
            'paciente',
            'dentista',
            'dentista__usuario',
            'especialidad',
            'cubiculo'
        )
    else:
        # Sin clínica, no mostrar nada
        queryset = Cita.objects.none()
    
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


@login_required
@require_http_methods(["GET"])
def buscar_pacientes(request):
    """
    Endpoint AJAX para buscar pacientes.
    Retorna JSON con lista de pacientes que coinciden con la búsqueda.
    Compatible con Select2.
    Busca por: nombres, apellidos o cédula.
    Tenant-aware: solo pacientes de la clínica activa.
    """
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    
    from pacientes.models import Paciente
    
    # Filtrar por clínica activa
    clinica = get_clinica_from_request(request)
    if not clinica:
        return JsonResponse({'results': [], 'total_count': 0, 'pagination': {'more': False}})
    
    if not query or len(query) < 1:
        # Mostrar pacientes recientes de la clínica si no hay búsqueda
        pacientes = Paciente.objects.filter(
            estado=True,
            clinica=clinica
        ).order_by('-id')[:10]
    else:
        # Buscar en nombre, apellido o cédula dentro de la clínica
        pacientes = Paciente.objects.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(cedula__icontains=query),
            estado=True,
            clinica=clinica
        ).order_by('apellidos', 'nombres')
    
    # Paginación
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    total_count = pacientes.count() if hasattr(pacientes, 'count') else len(pacientes)
    pacientes_page = list(pacientes[start:end])
    
    print(f"[DEBUG] Pagina {page}: mostrando {len(pacientes_page)} de {total_count}")
    
    results = [{
        'id': p.id,
        'text': f"{p.nombres} {p.apellidos}",
        'cedula': p.cedula,
        'nombres': p.nombres,
        'apellidos': p.apellidos,
        'es_vip': p.es_vip,
        'categoria_vip': p.categoria_vip,
        'tiene_enfermedades_criticas': p.tiene_enfermedades_criticas(),
        'nivel_alerta': p.calcular_nivel_alerta()
    } for p in pacientes_page]
    
    response = {
        'results': results,
        'total_count': total_count,
        'pagination': {
            'more': (page * per_page) < total_count
        }
    }
    
    print(f"[DEBUG] Retornando: {response}")
    
    return JsonResponse(response)



# ==================== VISTAS DE ESPECIALIDADES ====================

class EspecialidadListView(LoginRequiredMixin, ListView):
    """
    Vista para listar todas las especialidades.
    Incluye búsqueda y filtrado por estado.
    """
    model = Especialidad
    template_name = 'cit/especialidad_list.html'
    context_object_name = 'especialidades'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Especialidad.objects.all().order_by('nombre')
        
        # Búsqueda
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '')
        if estado == 'activas':
            queryset = queryset.filter(estado=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(estado=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['estado_filtro'] = self.request.GET.get('estado', '')
        context['total_especialidades'] = Especialidad.objects.count()
        context['especialidades_activas'] = Especialidad.objects.filter(estado=True).count()
        return context


class EspecialidadCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear una nueva especialidad.
    """
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'cit/especialidad_form.html'
    success_url = reverse_lazy('cit:especialidad-list')
    
    def form_valid(self, form):
        # Asignar usuario creador
        form.instance.uc = self.request.user
        messages.success(
            self.request, 
            f'✅ Especialidad "{form.instance.nombre}" creada exitosamente'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            '❌ Error al crear la especialidad. Por favor revise los campos.'
        )
        return super().form_invalid(form)


class EspecialidadUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar una especialidad existente.
    """
    model = Especialidad
    form_class = EspecialidadForm
    template_name = 'cit/especialidad_form.html'
    success_url = reverse_lazy('cit:especialidad-list')
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'✅ Especialidad "{form.instance.nombre}" actualizada exitosamente'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request, 
            '❌ Error al actualizar la especialidad. Por favor revise los campos.'
        )
        return super().form_invalid(form)


class EspecialidadDeleteView(LoginRequiredMixin, DeleteView):
    """
    Vista para eliminar (soft delete) una especialidad.
    Cambia el estado a False en lugar de eliminar el registro.
    """
    model = Especialidad
    template_name = 'cit/especialidad_confirm_delete.html'
    success_url = reverse_lazy('cit:especialidad-list')
    
    def form_valid(self, form):
        """Sobrescribir para hacer soft delete en lugar de eliminar"""
        self.object = self.get_object()
        
        # Soft delete: cambiar estado en lugar de eliminar
        self.object.estado = False
        self.object.save()
        
        messages.success(
            self.request, 
            f'✅ Especialidad "{self.object.nombre}" desactivada exitosamente'
        )
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si hay dentistas o citas asociadas
        context['dentistas_count'] = self.object.dentistas.count()
        context['citas_count'] = self.object.citas.count()
        return context


# ============================================================================
# VISTAS CRUD DE DENTISTAS CON GESTIÓN DE HORARIOS
# ============================================================================

class DentistaListView(LoginRequiredMixin, ListView):
    """
    Vista para listar dentistas con búsqueda y filtros.
    Tenant-aware: solo muestra dentistas de la clínica activa.
    """
    model = Dentista
    template_name = 'cit/dentista_list.html'
    context_object_name = 'dentistas'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar por clínica activa y aplicar búsqueda/filtros"""
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Dentista.objects.none()
        
        queryset = Dentista.objects.filter(
            sucursal_principal__clinica=clinica
        ).select_related(
            'usuario',
            'sucursal_principal',
            'sucursal_principal__clinica'
        ).prefetch_related('especialidades')
        
        # Filtro por especialidad
        especialidad_id = self.request.GET.get('especialidad')
        if especialidad_id:
            queryset = queryset.filter(especialidades__id=especialidad_id)
        
        # Filtro por sucursal (ya restringido a la clínica)
        sucursal_id = self.request.GET.get('sucursal')
        if sucursal_id:
            queryset = queryset.filter(sucursal_principal_id=sucursal_id)
        
        # Búsqueda por nombre, cédula o licencia
        busqueda = self.request.GET.get('q')
        if busqueda:
            queryset = queryset.filter(
                Q(usuario__first_name__icontains=busqueda) |
                Q(usuario__last_name__icontains=busqueda) |
                Q(cedula_profesional__icontains=busqueda) |
                Q(numero_licencia__icontains=busqueda)
            )
        
        return queryset.order_by('usuario__last_name', 'usuario__first_name')
    
    def get_context_data(self, **kwargs):
        """Agregar datos adicionales al contexto (solo de la clínica)"""
        context = super().get_context_data(**kwargs)
        clinica = get_clinica_from_request(self.request)
        
        context['especialidades'] = Especialidad.objects.filter(estado=True)
        
        # Solo sucursales de la clínica activa
        from .models import Sucursal
        if clinica:
            context['sucursales'] = Sucursal.objects.filter(
                estado=True, 
                clinica=clinica
            ).select_related('clinica')
        else:
            context['sucursales'] = Sucursal.objects.none()
        
        return context


class DentistaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo dentista con horarios.
    Maneja el formulario principal y dos formsets inline.
    """
    model = Dentista
    template_name = 'cit/dentista_form.html'
    success_url = reverse_lazy('cit:dentista-list')
    
    def get_form_class(self):
        from .forms import DentistaForm
        return DentistaForm
    
    def get_context_data(self, **kwargs):
        """Agregar formsets al contexto"""
        context = super().get_context_data(**kwargs)
        
        from .models import Sucursal, ConfiguracionClinica
        from .forms import (
            DisponibilidadDentistaFormSet, 
            ExcepcionDisponibilidadFormSet,
            ComisionDentistaFormSet
        )
        
        # Determinar sucursales disponibles
        if self.object and self.object.pk:
            sucursales = self.object.sucursales.all()
            if not sucursales.exists():
                sucursales = Sucursal.objects.filter(estado=True)
        else:
            sucursales = Sucursal.objects.filter(estado=True)
        
        # Determinar especialidades disponibles para comisiones
        if self.object and self.object.pk:
            especialidades = self.object.especialidades.all()
        else:
            especialidades = None
        
        if self.request.POST:
            disponibilidad_formset = DisponibilidadDentistaFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'sucursales_queryset': sucursales}
            )
            excepcion_formset = ExcepcionDisponibilidadFormSet(
                self.request.POST,
                instance=self.object
            )
            comision_formset = ComisionDentistaFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            default_sucursal = sucursales.first() if sucursales.exists() else None

            # Prefill weekly schedule using clinic hours (Mon-Fri by default)
            initial_disponibilidades = []
            try:
                config = ConfiguracionClinica.objects.filter(estado=True).first()
            except Exception:
                config = None

            if config:
                dias_atiende = config.get_dias_atencion()
                for dia in dias_atiende:
                    horario = config.get_horario_dia(dia)
                    if horario:
                        initial_disponibilidades.append({
                            'dia_semana': dia,
                            'hora_inicio': horario[0],
                            'hora_fin': horario[1],
                            'activo': True,
                            'sucursal': default_sucursal
                        })

            if not initial_disponibilidades:
                default_inicio = datetime.strptime('08:30', '%H:%M').time()
                default_fin = datetime.strptime('18:00', '%H:%M').time()
                for dia in range(5):  # Lunes a Viernes
                    initial_disponibilidades.append({
                        'dia_semana': dia,
                        'hora_inicio': default_inicio,
                        'hora_fin': default_fin,
                        'activo': True,
                        'sucursal': default_sucursal
                    })

            disponibilidad_formset = DisponibilidadDentistaFormSet(
                instance=self.object,
                form_kwargs={'sucursales_queryset': sucursales},
                initial=initial_disponibilidades
            )
            excepcion_formset = ExcepcionDisponibilidadFormSet(
                instance=self.object
            )
            comision_formset = ComisionDentistaFormSet(
                instance=self.object
            )
        
        context['disponibilidad_formset'] = disponibilidad_formset
        context['excepcion_formset'] = excepcion_formset
        context['comision_formset'] = comision_formset
        
        return context
    
    def form_valid(self, form):
        """Validar y guardar formsets junto con el formulario principal"""
        context = self.get_context_data()
        disponibilidad_formset = context['disponibilidad_formset']
        excepcion_formset = context['excepcion_formset']
        comision_formset = context['comision_formset']
        
        # Validar todos los formsets
        if disponibilidad_formset.is_valid() and excepcion_formset.is_valid() and comision_formset.is_valid():
            # Guardar el dentista primero, pasando el usuario actual para uc
            self.object = form.save(user=self.request.user)
            
            # ========== AUTO-CREAR UsuarioClinica (SOOD-USU-007) ==========
            try:
                from usuarios.models import UsuarioClinica, RolUsuario
                
                # Obtener clínica del dentista
                clinica = self.object.sucursal_principal.clinica if self.object.sucursal_principal else None
                
                if clinica:
                    # Verificar si ya existe UsuarioClinica
                    usuario_clinica, created = UsuarioClinica.objects.get_or_create(
                        usuario=self.object.usuario,
                        defaults={
                            'clinica': clinica,
                            'rol': RolUsuario.ODONTOLOGO,
                            'activo': True
                        }
                    )
                    
                    if created:
                        messages.info(
                            self.request,
                            f'✅ Usuario clínica creado automáticamente para Dr(a). {self.object.usuario.get_full_name()} con rol Odontólogo'
                        )
                    else:
                        # Si ya existe, actualizar clínica y rol si es necesario
                        if usuario_clinica.clinica != clinica or usuario_clinica.rol != RolUsuario.ODONTOLOGO:
                            usuario_clinica.clinica = clinica
                            usuario_clinica.rol = RolUsuario.ODONTOLOGO
                            usuario_clinica.save()
                            messages.info(
                                self.request,
                                f'✅ Usuario clínica actualizado para Dr(a). {self.object.usuario.get_full_name()}'
                            )
            except Exception as e:
                messages.warning(
                    self.request,
                    f'⚠️ No se pudo crear UsuarioClinica automáticamente: {str(e)}'
                )
            # ============================================================
            
            # Guardar los formsets, excluyendo horarios vacíos e inactivos
            disponibilidad_formset.instance = self.object
            disponibilidades = disponibilidad_formset.save(commit=False)
            
            for disponibilidad in disponibilidades:
                # Solo guardar si tiene horarios definidos
                if disponibilidad.hora_inicio and disponibilidad.hora_fin:
                    # Asignar usuario creador si es nuevo
                    if not disponibilidad.pk:
                        disponibilidad.uc = self.request.user
                    disponibilidad.save()
            
            # Eliminar los marcados para eliminar
            for obj in disponibilidad_formset.deleted_objects:
                obj.delete()
            
            # Guardar excepciones con uc asignado
            excepcion_formset.instance = self.object
            excepciones = excepcion_formset.save(commit=False)
            
            for excepcion in excepciones:
                # Solo guardar si está activa (Aplicar marcado) y tiene datos válidos
                if excepcion.estado and excepcion.fecha_inicio and excepcion.fecha_fin:
                    # Asignar usuario creador si es nuevo
                    if not excepcion.pk:
                        excepcion.uc = self.request.user
                    excepcion.save()
            
            # Eliminar excepciones marcadas para eliminar
            for obj in excepcion_formset.deleted_objects:
                obj.delete()
            
            # Guardar comisiones
            comision_formset.instance = self.object
            comisiones = comision_formset.save(commit=False)
            
            for comision in comisiones:
                # Asignar usuario creador si es nuevo
                if not comision.pk:
                    comision.uc = self.request.user
                comision.save()
            
            # Eliminar comisiones marcadas para eliminar
            for obj in comision_formset.deleted_objects:
                obj.delete()
            
            messages.success(
                self.request,
                f'✅ Dentista Dr(a). {self.object.usuario.get_full_name()} creado exitosamente'
            )
            return redirect(self.success_url)
        else:
            # Mostrar errores de los formsets de forma legible
            error_found = False
            
            if not disponibilidad_formset.is_valid():
                error_found = True
                for form in disponibilidad_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Horarios - {field_name}: {error}')
            
            if not excepcion_formset.is_valid():
                error_found = True
                for form in excepcion_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Excepciones - {field_name}: {error}')
            
            if not comision_formset.is_valid():
                error_found = True
                for form in comision_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Comisiones - {field_name}: {error}')
            
            if not error_found:
                messages.error(self.request, '❌ Error al crear el dentista. Por favor revise todos los campos.')
            
            return self.form_invalid(form)


class DentistaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vista para actualizar un dentista existente con sus horarios.
    """
    model = Dentista
    template_name = 'cit/dentista_form.html'
    success_url = reverse_lazy('cit:dentista-list')
    
    def get_form_class(self):
        from .forms import DentistaForm
        return DentistaForm
    
    def get_context_data(self, **kwargs):
        """Agregar formsets al contexto"""
        context = super().get_context_data(**kwargs)
        
        from .models import Sucursal
        from .forms import (
            DisponibilidadDentistaFormSet, 
            ExcepcionDisponibilidadFormSet,
            ComisionDentistaFormSet
        )
        
        # Determinar sucursales disponibles
        sucursales = self.object.sucursales.all()
        if not sucursales.exists():
            sucursales = Sucursal.objects.filter(estado=True)
        
        # Determinar especialidades disponibles para comisiones
        especialidades = self.object.especialidades.all()
        
        # Si se pasan formsets como kwargs, usarlos (para preservar errores)
        if 'disponibilidad_formset' in kwargs:
            context['disponibilidad_formset'] = kwargs['disponibilidad_formset']
        elif self.request.POST:
            context['disponibilidad_formset'] = DisponibilidadDentistaFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'sucursales_queryset': sucursales}
            )
        else:
            context['disponibilidad_formset'] = DisponibilidadDentistaFormSet(
                instance=self.object,
                form_kwargs={'sucursales_queryset': sucursales}
            )
        
        if 'excepcion_formset' in kwargs:
            context['excepcion_formset'] = kwargs['excepcion_formset']
        elif self.request.POST:
            context['excepcion_formset'] = ExcepcionDisponibilidadFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['excepcion_formset'] = ExcepcionDisponibilidadFormSet(
                instance=self.object
            )
        
        if 'comision_formset' in kwargs:
            context['comision_formset'] = kwargs['comision_formset']
        elif self.request.POST:
            context['comision_formset'] = ComisionDentistaFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['comision_formset'] = ComisionDentistaFormSet(
                instance=self.object
            )
        
        # Agregar el tab activo al contexto (por defecto 'datos')
        context['active_tab'] = kwargs.get('active_tab', 'datos')
        
        return context
    
    def form_valid(self, form):
        """Validar y guardar formsets junto con el formulario principal"""
        context = self.get_context_data()
        disponibilidad_formset = context['disponibilidad_formset']
        excepcion_formset = context['excepcion_formset']
        comision_formset = context['comision_formset']
        
        # Validar todos los formsets
        if disponibilidad_formset.is_valid() and excepcion_formset.is_valid() and comision_formset.is_valid():
            
            # VALIDACIÓN PREVIA: Verificar duplicados de especialidades activas ANTES de guardar
            comisiones_a_guardar = []
            for form_comision in comision_formset:
                if form_comision.cleaned_data and not form_comision.cleaned_data.get('DELETE', False):
                    comisiones_a_guardar.append(form_comision.cleaned_data)
            
            # Validar que no haya especialidades duplicadas activas
            especialidades_activas = {}
            has_duplicate = False
            duplicate_especialidad = None
            
            for comision_data in comisiones_a_guardar:
                activo = comision_data.get('activo', False)
                especialidad = comision_data.get('especialidad')
                
                if activo and especialidad:
                    if especialidad.id in especialidades_activas:
                        has_duplicate = True
                        duplicate_especialidad = especialidad.nombre
                        break
                    especialidades_activas[especialidad.id] = True
            
            # Si hay duplicados, mostrar error SIN guardar nada
            if has_duplicate:
                messages.error(
                    self.request,
                    f'❌ Ya existe una comisión activa para {duplicate_especialidad}. '
                    f'Debe desactivar la comisión existente antes de activar esta.'
                )
                # No renderizar, sino usar form_invalid para mantener el estado
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        active_tab='comisiones',
                        disponibilidad_formset=disponibilidad_formset,
                        excepcion_formset=excepcion_formset,
                        comision_formset=comision_formset
                    )
                )
            
            # Si pasa la validación, AHORA sí guardar el dentista
            self.object = form.save(user=self.request.user)
            
            # Actualizar usuario modificador
            self.object.um = self.request.user.id
            self.object.save()
            
            # Guardar los formsets, excluyendo horarios vacíos e inactivos
            disponibilidad_formset.instance = self.object
            disponibilidades = disponibilidad_formset.save(commit=False)
            
            for disponibilidad in disponibilidades:
                # Solo guardar si tiene horarios definidos
                if disponibilidad.hora_inicio and disponibilidad.hora_fin:
                    # Asignar usuario creador si es nuevo
                    if not disponibilidad.pk:
                        disponibilidad.uc = self.request.user
                    else:
                        # Actualizar usuario modificador
                        disponibilidad.um = self.request.user.id
                    disponibilidad.save()
            
            # Eliminar los marcados para eliminar
            for obj in disponibilidad_formset.deleted_objects:
                obj.delete()
            
            # Guardar excepciones con uc/um asignado
            excepcion_formset.instance = self.object
            excepciones = excepcion_formset.save(commit=False)
            
            for excepcion in excepciones:
                # Solo guardar si está activa (Aplicar marcado) y tiene datos válidos
                if excepcion.estado and excepcion.fecha_inicio and excepcion.fecha_fin:
                    # Asignar usuario creador si es nuevo, modificador si es existente
                    if not excepcion.pk:
                        excepcion.uc = self.request.user
                    else:
                        excepcion.um = self.request.user.id
                    excepcion.save()
                elif excepcion.pk and not excepcion.estado:
                    # Si existe en BD pero está desactivada, eliminarla
                    excepcion.delete()
            
            # Eliminar excepciones marcadas para eliminar
            for obj in excepcion_formset.deleted_objects:
                obj.delete()
            
            # Guardar comisiones (ya validadas previamente)
            comision_formset.instance = self.object
            comisiones = comision_formset.save(commit=False)
            
            # Guardar cada comisión con usuario creador/modificador
            for comision in comisiones:
                # Asignar usuario creador si es nuevo, modificador si es existente
                if not comision.pk:
                    comision.uc = self.request.user
                else:
                    comision.um = self.request.user.id
                comision.save()
            
            # Eliminar comisiones marcadas para eliminar
            for obj in comision_formset.deleted_objects:
                obj.delete()
            
            messages.success(
                self.request,
                f'✅ Dentista Dr(a). {self.object.usuario.get_full_name()} actualizado exitosamente'
            )
            return redirect(self.success_url)
        else:
            # Mostrar errores de los formsets de forma legible
            error_found = False
            
            if not disponibilidad_formset.is_valid():
                error_found = True
                for form in disponibilidad_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Horarios - {field_name}: {error}')
            
            if not excepcion_formset.is_valid():
                error_found = True
                for form in excepcion_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Excepciones - {field_name}: {error}')
            
            if not comision_formset.is_valid():
                error_found = True
                for form in comision_formset:
                    if form.errors:
                        for field, errors in form.errors.items():
                            field_name = field.replace('_', ' ').title()
                            for error in errors:
                                messages.error(self.request, f'Comisiones - {field_name}: {error}')
            
            if not error_found:
                messages.error(self.request, '❌ Error al actualizar el dentista. Por favor revise todos los campos.')
            
            return self.form_invalid(form)


class DentistaDeleteView(LoginRequiredMixin, DeleteView):
    """
    Vista para eliminar (soft delete) un dentista.
    Muestra advertencia si tiene citas programadas.
    """
    model = Dentista
    template_name = 'cit/dentista_confirm_delete.html'
    success_url = reverse_lazy('cit:dentista-list')
    
    def form_valid(self, form):
        """Sobrescribir para hacer soft delete"""
        self.object = self.get_object()
        
        # Verificar si tiene citas futuras
        citas_futuras = Cita.objects.filter(
            dentista=self.object,
            fecha_hora__gte=timezone.now(),
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]
        ).count()
        
        if citas_futuras > 0:
            messages.warning(
                self.request,
                f'⚠️ El dentista tiene {citas_futuras} cita(s) programada(s). Se recomienda reasignarlas antes de desactivar.'
            )
        
        # Soft delete
        self.object.estado = False
        self.object.save()
        
        messages.success(
            self.request,
            f'✅ Dentista Dr(a). {self.object.usuario.get_full_name()} desactivado exitosamente'
        )
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Información sobre impacto
        context['citas_totales'] = self.object.citas.count()
        context['citas_futuras'] = Cita.objects.filter(
            dentista=self.object,
            fecha_hora__gte=timezone.now(),
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA]
        ).count()
        context['disponibilidades_count'] = self.object.disponibilidades.count()
        context['excepciones_count'] = self.object.excepciones.count()
        
        return context


# ============================================================================
# VISTAS CRUD DE CLÍNICAS
# ============================================================================

from .models import Clinica, Sucursal
from .forms import ClinicaForm


class ClinicaListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las clínicas"""
    model = Clinica
    template_name = 'cit/clinica_list.html'
    context_object_name = 'clinicas'
    paginate_by = 20
    
    def get_queryset(self):
        """Aplicar filtros y búsqueda"""
        queryset = Clinica.objects.prefetch_related('sucursales').all()
        
        # Búsqueda por nombre, dirección o email
        busqueda = self.request.GET.get('busqueda')
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(direccion__icontains=busqueda) |
                Q(email__icontains=busqueda) |
                Q(telefono__icontains=busqueda)
            )
        
        return queryset.order_by('-fc')  # Más recientes primero
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busqueda'] = self.request.GET.get('busqueda', '')
        context['total_clinicas'] = self.get_queryset().count()
        return context


class ClinicaDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de una clínica"""
    model = Clinica
    template_name = 'cit/clinica_detail.html'
    context_object_name = 'clinica'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sucursales = self.object.sucursales.all().order_by('nombre')
        
        # Convertir días_atencion a badges legibles
        dias_map = {'L': 'L', 'M': 'M', 'X': 'X', 'J': 'J', 'V': 'V', 'S': 'S', 'D': 'D'}
        for sucursal in sucursales:
            if sucursal.dias_atencion:
                sucursal.dias_badges = [dias_map.get(d, d) for d in sucursal.dias_atencion if d in dias_map]
            else:
                sucursal.dias_badges = []
        
        context['sucursales'] = sucursales
        context['total_sucursales'] = sucursales.count()
        return context


class ClinicaCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva clínica"""
    model = Clinica
    form_class = ClinicaForm
    template_name = 'cit/clinica_form.html'
    success_url = reverse_lazy('cit:clinica-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def form_valid(self, form):
        # Asignar el usuario creador
        form.instance.uc = self.request.user
        messages.success(self.request, f'Clínica "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)


class ClinicaUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar una clínica existente"""
    model = Clinica
    form_class = ClinicaForm
    template_name = 'cit/clinica_form.html'
    success_url = reverse_lazy('cit:clinica-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def form_valid(self, form):
        # Asignar el usuario que modifica
        form.instance.um = self.request.user.id
        messages.success(self.request, f'Clínica "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context


class ClinicaDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar (desactivar) una clínica"""
    model = Clinica
    template_name = 'cit/clinica_confirm_delete.html'
    success_url = reverse_lazy('cit:clinica-list')
    context_object_name = 'clinica'
    
    def post(self, request, *args, **kwargs):
        """Manejar POST: validar y realizar soft delete"""
        self.object = self.get_object()
        
        # Verificar si tiene sucursales activas
        sucursales_activas = self.object.sucursales.filter(estado=True).count()
        if sucursales_activas > 0:
            messages.error(
                request,
                f'No se puede eliminar la clínica "{self.object.nombre}" porque tiene {sucursales_activas} sucursal(es) activa(s). '
                'Primero debe desactivar todas las sucursales.'
            )
            return redirect('cit:clinica-detail', pk=self.object.pk)
        
        # Soft delete: cambiar estado en lugar de eliminar
        self.object.estado = False
        self.object.um = request.user.id
        self.object.save()
        
        messages.success(request, f'Clínica "{self.object.nombre}" desactivada exitosamente.')
        return redirect(self.success_url)


class ClinicaActivateView(LoginRequiredMixin, View):
    """Vista para reactivar una clínica desactivada"""
    
    def post(self, request, pk):
        """Reactivar la clínica"""
        clinica = get_object_or_404(Clinica, pk=pk)
        
        if clinica.estado:
            messages.warning(request, f'La clínica "{clinica.nombre}" ya está activa.')
        else:
            clinica.estado = True
            clinica.um = request.user.id
            clinica.save()
            messages.success(request, f'Clínica "{clinica.nombre}" reactivada exitosamente.')
        
        return redirect('cit:clinica-detail', pk=pk)


class ClinicaSelectView(LoginRequiredMixin, View):
    """Vista para seleccionar la clínica activa en la sesión"""
    template_name = 'cit/clinica_select.html'
    
    def get(self, request):
        """Mostrar el selector de clínicas"""
        # Admin ve TODAS las clínicas, usuarios regulares solo ven activas
        if request.user.is_staff and request.user.is_superuser:
            clinicas = list(Clinica.objects.all().order_by('nombre'))
            es_admin = True
        else:
            clinicas = list(Clinica.objects.filter(estado=True).order_by('nombre'))
            es_admin = False
        
        clinica_actual_id = request.session.get('clinica_id')
        
        context = {
            'clinicas': clinicas,
            'clinica_actual_id': clinica_actual_id,
            'es_admin': es_admin,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Guardar la clínica seleccionada en la sesión"""
        clinica_id = request.POST.get('clinica_id')
        
        if not clinica_id:
            messages.error(request, 'Debe seleccionar una clínica.')
            return redirect('cit:clinica-seleccionar')
        
        try:
            # Admin puede seleccionar cualquier clínica, usuarios regulares solo activas
            if request.user.is_staff and request.user.is_superuser:
                clinica = Clinica.objects.get(pk=clinica_id)
            else:
                clinica = Clinica.objects.get(pk=clinica_id, estado=True)
            
            request.session['clinica_id'] = clinica.id
            messages.success(request, f'Clínica "{clinica.nombre}" seleccionada.')
            
            # Redirigir a la página de inicio o la que estaba intentando acceder
            next_url = request.GET.get('next', reverse('bases:home'))
            return redirect(next_url)
            
        except Clinica.DoesNotExist:
            messages.error(request, 'La clínica seleccionada no existe o está inactiva.')
            return redirect('cit:clinica-seleccionar')


# ============================================================================
# VISTAS CRUD DE SUCURSALES
# ============================================================================

class SucursalListView(LoginRequiredMixin, ListView):
    """
    Vista para listar sucursales.
    Tenant-aware: solo muestra sucursales de la clínica activa.
    """
    model = Sucursal
    template_name = 'cit/sucursal_list.html'
    context_object_name = 'sucursales'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar por clínica activa y aplicar búsqueda"""
        clinica = get_clinica_from_request(self.request)
        if not clinica:
            return Sucursal.objects.none()
        
        queryset = Sucursal.objects.filter(
            clinica=clinica
        ).select_related('clinica')
        
        # Búsqueda general
        busqueda = self.request.GET.get('busqueda')
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(direccion__icontains=busqueda) |
                Q(telefono__icontains=busqueda)
            )
        
        return queryset.order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Procesar días de atención para cada sucursal
        dias_map = {'L': 'L', 'M': 'M', 'X': 'X', 'J': 'J', 'V': 'V', 'S': 'S', 'D': 'D'}
        if 'object_list' in context:
            for sucursal in context['object_list']:
                if sucursal.dias_atencion:
                    sucursal.dias_badges = [dias_map.get(d, d) for d in sucursal.dias_atencion if d in dias_map]
                else:
                    sucursal.dias_badges = []
        
        context['total_sucursales'] = self.get_queryset().count()
        context['busqueda'] = self.request.GET.get('busqueda', '')
        return context


class SucursalDetailView(LoginRequiredMixin, DetailView):
    """Vista para mostrar detalles de una sucursal"""
    model = Sucursal
    template_name = 'cit/sucursal_detail.html'
    context_object_name = 'sucursal'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Convertir string "LMXJV" a lista legible
        dias_map = {'L': 'Lunes', 'M': 'Martes', 'X': 'Miércoles', 
                    'J': 'Jueves', 'V': 'Viernes', 'S': 'Sábado', 'D': 'Domingo'}
        if self.object.dias_atencion:
            context['dias_atencion_lista'] = [dias_map.get(d, d) for d in self.object.dias_atencion]
        else:
            context['dias_atencion_lista'] = []
        return context


class SucursalCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva sucursal"""
    model = Sucursal
    form_class = SucursalForm
    template_name = 'cit/sucursal_form.html'
    success_url = reverse_lazy('cit:sucursal-list')
    
    def get_initial(self):
        """Pre-llenar clínica si viene del detalle de clínica"""
        initial = super().get_initial()
        clinica_id = self.request.GET.get('clinica')
        if clinica_id:
            initial['clinica'] = clinica_id
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import CubiculoFormSet
        cubiculo_formset = kwargs.get('cubiculo_formset')

        if cubiculo_formset is not None:
            context['cubiculo_formset'] = cubiculo_formset
        elif self.request.method == 'POST' and 'cubiculo_set-TOTAL_FORMS' in self.request.POST:
            context['cubiculo_formset'] = CubiculoFormSet(self.request.POST)
        else:
            context['cubiculo_formset'] = CubiculoFormSet()
        return context

    def form_valid(self, form):
        from .forms import CubiculoFormSet
        with transaction.atomic():
            form.instance.uc = self.request.user
            self.object = form.save()

            cubiculo_formset = CubiculoFormSet(self.request.POST, instance=self.object)

            if cubiculo_formset.is_valid():
                cubiculos = cubiculo_formset.save(commit=False)
                for cubiculo in cubiculos:
                    cubiculo.uc = self.request.user
                    cubiculo.um = self.request.user.id
                    cubiculo.save()
                cubiculo_formset.save_m2m()
                for obj in cubiculo_formset.deleted_objects:
                    obj.delete()

                messages.success(
                    self.request,
                    f'Sucursal "{self.object.nombre}" creada exitosamente para {self.object.clinica.nombre}.'
                )
                return redirect(self.success_url)

            transaction.set_rollback(True)

        messages.error(self.request, 'Por favor corrija los errores en los cubículos.')
        return self.form_invalid(form)

    def form_invalid(self, form):
        from .forms import CubiculoFormSet
        if self.request.method == 'POST' and 'cubiculo_set-TOTAL_FORMS' in self.request.POST:
            cubiculo_formset = CubiculoFormSet(self.request.POST, instance=form.instance)
        else:
            cubiculo_formset = CubiculoFormSet()
        messages.error(self.request, 'Por favor corrija los errores en el formulario y los cubículos.')
        return self.render_to_response(self.get_context_data(form=form, cubiculo_formset=cubiculo_formset))


class SucursalUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar una sucursal existente"""
    model = Sucursal
    form_class = SucursalForm
    template_name = 'cit/sucursal_form.html'
    success_url = reverse_lazy('cit:sucursal-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import CubiculoFormSet
        cubiculo_formset = kwargs.get('cubiculo_formset')

        if cubiculo_formset is not None:
            context['cubiculo_formset'] = cubiculo_formset
        elif self.request.method == 'POST' and 'cubiculo_set-TOTAL_FORMS' in self.request.POST:
            context['cubiculo_formset'] = CubiculoFormSet(self.request.POST, instance=self.object)
        else:
            context['cubiculo_formset'] = CubiculoFormSet(instance=self.object)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        from .forms import CubiculoFormSet
        from django.db import transaction
        cubiculo_formset = CubiculoFormSet(self.request.POST, instance=self.object)

        if not cubiculo_formset.is_valid():
            messages.error(self.request, 'Por favor corrija los errores en los cubículos.')
            return self.form_invalid(form)

        with transaction.atomic():
            form.instance.um = self.request.user.id
            self.object = form.save()

            cubiculo_formset.instance = self.object
            cubiculos = cubiculo_formset.save(commit=False)
            for cubiculo in cubiculos:
                if not cubiculo.pk:
                    cubiculo.uc = self.request.user
                cubiculo.um = self.request.user.id
                cubiculo.save()
            cubiculo_formset.save_m2m()
            for obj in cubiculo_formset.deleted_objects:
                obj.delete()

        messages.success(self.request, f'Sucursal "{self.object.nombre}" actualizada exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        from .forms import CubiculoFormSet
        if self.request.method == 'POST' and 'cubiculo_set-TOTAL_FORMS' in self.request.POST:
            cubiculo_formset = CubiculoFormSet(self.request.POST, instance=self.object)
        else:
            cubiculo_formset = CubiculoFormSet(instance=self.object)
        messages.error(self.request, 'Por favor corrija los errores en el formulario y los cubículos.')
        return self.render_to_response(self.get_context_data(form=form, cubiculo_formset=cubiculo_formset))


class SucursalDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar (desactivar) una sucursal"""
    model = Sucursal
    template_name = 'cit/sucursal_confirm_delete.html'
    success_url = reverse_lazy('cit:sucursal-list')
    context_object_name = 'sucursal'
    
    def form_valid(self, form):
        """Soft delete: cambiar estado a False en lugar de eliminar"""
        self.object = self.get_object()
        
        # Validar que no tenga citas futuras
        # Las citas están asociadas a cubículos, no directamente a sucursales
        # Por ahora omitimos esta validación y la implementaremos cuando
        # se relacione Cubiculo con Sucursal
        
        # Desactivar
        self.object.estado = False
        self.object.um = self.request.user.id
        self.object.save()
        
        messages.success(self.request, 
            f'Sucursal "{self.object.nombre}" desactivada exitosamente.')
        return redirect(self.success_url)


class SucursalActivateView(LoginRequiredMixin, View):
    """Vista para reactivar una sucursal desactivada"""
    
    def post(self, request, pk):
        """Reactivar la sucursal"""
        sucursal = get_object_or_404(Sucursal, pk=pk)
        
        if sucursal.estado:
            messages.warning(request, f'La sucursal "{sucursal.nombre}" ya está activa.')
        else:
            sucursal.estado = True
            sucursal.um = request.user.id
            sucursal.save()
            messages.success(request, f'Sucursal "{sucursal.nombre}" reactivada exitosamente.')
        
        return redirect('cit:sucursal-detail', pk=pk)

