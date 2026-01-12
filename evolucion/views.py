"""
Vistas para evolución odontológica.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator

from evolucion.models import (
    EvolucionConsulta,
    PlanTratamiento,
    ProcedimientoEnEvolucion,
)
from evolucion.forms import (
    EvolucionConsultaForm,
    ProcedimientoEnEvolucionForm,
    PlanTratamientoForm,
    ProcedimientoEnPlanForm,
    BuscarEvolucionForm,
    HistoriaClinicaOdontologicaForm,
    ProcedimientoEnEvolucionFormSet,
    ProcedimientoEnPlanFormSet,
)
from evolucion import services
from pacientes.models import Paciente


@login_required
def lista_evoluciones(request):
    """
    Listado de evoluciones del paciente con filtros.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    evoluciones = services.evoluciones_para_clinica(clinica.id)
    
    # Formulario de búsqueda
    form = BuscarEvolucionForm(request.GET or None, clinica=clinica)
    
    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data.get('paciente'):
            evoluciones = evoluciones.filter(paciente=form.cleaned_data['paciente'])
        
        if form.cleaned_data.get('fecha_desde'):
            evoluciones = evoluciones.filter(fecha_consulta__gte=form.cleaned_data['fecha_desde'])
        
        if form.cleaned_data.get('fecha_hasta'):
            evoluciones = evoluciones.filter(fecha_consulta__lte=form.cleaned_data['fecha_hasta'])
        
        if form.cleaned_data.get('dentista'):
            evoluciones = evoluciones.filter(dentista=form.cleaned_data['dentista'])
    
    # Estadísticas
    total_evoluciones = evoluciones.count()
    evoluciones_mes = evoluciones.filter(
        fecha_consulta__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Paginación
    paginator = Paginator(evoluciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_evoluciones': total_evoluciones,
        'evoluciones_mes': evoluciones_mes,
    }
    
    return render(request, 'evolucion/lista_evoluciones.html', context)


@login_required
def detalle_evolucion(request, pk):
    """
    Detalle completo de una evolución.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    evolucion = services.obtener_evolucion_para_clinica(pk, clinica.id)
    
    if not evolucion:
        messages.error(request, 'Evolución no encontrada o sin acceso.')
        return redirect('evolucion:lista')
    
    # Obtener odontograma del paciente
    odontograma = evolucion.paciente.odontograma if hasattr(evolucion.paciente, 'odontograma') else None
    
    context = {
        'evolucion': evolucion,
        'odontograma': odontograma,
        'procedimientos': evolucion.procedimientos.all(),
    }
    
    return render(request, 'evolucion/detalle_evolucion.html', context)


@login_required
def nueva_evolucion(request, paciente_id):
    """
    Crear una nueva evolución para un paciente.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica=clinica)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('evolucion:lista')
    
    if request.method == 'POST':
        form = EvolucionConsultaForm(request.POST, paciente=paciente, clinica=clinica)
        
        if form.is_valid():
            with transaction.atomic():
                evolucion = form.save(commit=False)
                evolucion.paciente = paciente
                evolucion.uc = request.user
                evolucion.save()
            
            messages.success(request, 'Evolución creada exitosamente.')
            return redirect('evolucion:detalle', pk=evolucion.pk)
    else:
        form = EvolucionConsultaForm(paciente=paciente, clinica=clinica)
    
    context = {
        'form': form,
        'paciente': paciente,
        'titulo': 'Nueva Evolución',
    }
    
    return render(request, 'evolucion/form_evolucion.html', context)


@login_required
def editar_evolucion(request, pk):
    """
    Editar una evolución existente.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    evolucion = services.obtener_evolucion_para_clinica(pk, clinica.id)
    
    if not evolucion:
        messages.error(request, 'Evolución no encontrada.')
        return redirect('evolucion:lista')
    
    if request.method == 'POST':
        form = EvolucionConsultaForm(
            request.POST,
            instance=evolucion,
            paciente=evolucion.paciente,
            clinica=clinica
        )
        
        if form.is_valid():
            evolucion = form.save(commit=False)
            evolucion.um = request.user
            evolucion.save()
            
            messages.success(request, 'Evolución actualizada exitosamente.')
            return redirect('evolucion:detalle', pk=evolucion.pk)
    else:
        form = EvolucionConsultaForm(
            instance=evolucion,
            paciente=evolucion.paciente,
            clinica=clinica
        )
    
    context = {
        'form': form,
        'evolucion': evolucion,
        'titulo': 'Editar Evolución',
    }
    
    return render(request, 'evolucion/form_evolucion.html', context)


@login_required
def editar_procedimientos_evolucion(request, pk):
    """
    Editar procedimientos de una evolución con formset.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    evolucion = services.obtener_evolucion_para_clinica(pk, clinica.id)
    
    if not evolucion:
        messages.error(request, 'Evolución no encontrada.')
        return redirect('evolucion:lista')
    
    if request.method == 'POST':
        formset = ProcedimientoEnEvolucionFormSet(request.POST, instance=evolucion)
        
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Procedimientos actualizados exitosamente.')
            return redirect('evolucion:detalle', pk=evolucion.pk)
    else:
        formset = ProcedimientoEnEvolucionFormSet(instance=evolucion)
    
    context = {
        'formset': formset,
        'evolucion': evolucion,
        'titulo': 'Editar Procedimientos',
    }
    
    return render(request, 'evolucion/editar_procedimientos_evolucion.html', context)


@login_required
@require_http_methods(["DELETE"])
def eliminar_procedimiento_evolucion(request, evolucion_pk, procedimiento_pk):
    """
    Eliminar un procedimiento de una evolución (AJAX).
    """
    if not hasattr(request.user, 'clinica'):
        return JsonResponse({'success': False, 'message': 'No autorizado'}, status=403)
    
    clinica = request.user.clinica
    
    success = services.eliminar_procedimiento_de_evolucion(
        evolucion_pk,
        clinica.id,
        procedimiento_pk
    )
    
    if success:
        messages.success(request, 'Procedimiento eliminado.')
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': 'Error al eliminar'}, status=400)


@login_required
def lista_planes(request):
    """
    Listado de planes de tratamiento.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    planes = services.planes_tratamiento_para_clinica(clinica.id)
    
    # Filtros
    estado = request.GET.get('estado')
    prioridad = request.GET.get('prioridad')
    
    if estado:
        planes = planes.filter(estado=estado)
    
    if prioridad:
        planes = planes.filter(prioridad=prioridad)
    
    # Estadísticas
    total_planes = planes.count()
    planes_activos = planes.filter(estado='ACTIVO').count()
    planes_pendientes = planes.filter(estado='PENDIENTE').count()
    
    # Paginación
    paginator = Paginator(planes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_planes': total_planes,
        'planes_activos': planes_activos,
        'planes_pendientes': planes_pendientes,
    }
    
    return render(request, 'evolucion/lista_planes.html', context)


@login_required
def detalle_plan(request, pk):
    """
    Detalle de un plan de tratamiento.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    plan = services.obtener_plan_para_clinica(pk, clinica.id)
    
    if not plan:
        messages.error(request, 'Plan no encontrado.')
        return redirect('evolucion:lista_planes')
    
    # Calcular progreso
    progreso = plan.get_progreso()
    
    context = {
        'plan': plan,
        'progreso': progreso,
        'procedimientos': plan.procedimientos.all(),
    }
    
    return render(request, 'evolucion/detalle_plan.html', context)


@login_required
def nuevo_plan(request, paciente_id):
    """
    Crear un nuevo plan de tratamiento.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica=clinica)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('evolucion:lista_planes')
    
    if request.method == 'POST':
        form = PlanTratamientoForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                plan = form.save(commit=False)
                plan.paciente = paciente
                plan.uc = request.user
                plan.save()
            
            messages.success(request, 'Plan creado exitosamente.')
            return redirect('evolucion:editar_plan', pk=plan.pk)
    else:
        form = PlanTratamientoForm()
    
    context = {
        'form': form,
        'paciente': paciente,
        'titulo': 'Nuevo Plan de Tratamiento',
    }
    
    return render(request, 'evolucion/form_plan.html', context)


@login_required
def editar_plan(request, pk):
    """
    Editar un plan de tratamiento existente.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    plan = services.obtener_plan_para_clinica(pk, clinica.id)
    
    if not plan:
        messages.error(request, 'Plan no encontrado.')
        return redirect('evolucion:lista_planes')
    
    if request.method == 'POST':
        form = PlanTratamientoForm(request.POST, instance=plan)
        
        if form.is_valid():
            plan = form.save(commit=False)
            plan.um = request.user
            plan.save()
            
            messages.success(request, 'Plan actualizado exitosamente.')
            return redirect('evolucion:detalle_plan', pk=plan.pk)
    else:
        form = PlanTratamientoForm(instance=plan)
    
    context = {
        'form': form,
        'plan': plan,
        'titulo': 'Editar Plan de Tratamiento',
    }
    
    return render(request, 'evolucion/form_plan.html', context)


@login_required
def editar_procedimientos_plan(request, pk):
    """
    Editar procedimientos de un plan con formset.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    plan = services.obtener_plan_para_clinica(pk, clinica.id)
    
    if not plan:
        messages.error(request, 'Plan no encontrado.')
        return redirect('evolucion:lista_planes')
    
    if request.method == 'POST':
        formset = ProcedimientoEnPlanFormSet(request.POST, instance=plan)
        
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Procedimientos actualizados exitosamente.')
            return redirect('evolucion:detalle_plan', pk=plan.pk)
    else:
        formset = ProcedimientoEnPlanFormSet(instance=plan)
    
    context = {
        'formset': formset,
        'plan': plan,
        'titulo': 'Editar Procedimientos del Plan',
    }
    
    return render(request, 'evolucion/editar_procedimientos_plan.html', context)


@login_required
def historia_clinica(request, paciente_id):
    """
    Ver/editar historia clínica de un paciente.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica=clinica)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('home')
    
    # Obtener o crear historia clínica
    historia, created = paciente.historia_clinica_odontologica.select_related(
        'paciente'
    ), True
    try:
        historia = paciente.historia_clinica_odontologica
        created = False
    except:
        from evolucion.models import HistoriaClinicaOdontologica
        historia = HistoriaClinicaOdontologica(
            paciente=paciente,
            uc=request.user
        )
        created = True
    
    if request.method == 'POST':
        form = HistoriaClinicaOdontologicaForm(request.POST, instance=historia)
        
        if form.is_valid():
            historia = form.save(commit=False)
            historia.paciente = paciente
            if created:
                historia.uc = request.user
            else:
                historia.um = request.user
            historia.save()
            
            messages.success(request, 'Historia clínica actualizada exitosamente.')
            return redirect('evolucion:detalle_historia', paciente_id=paciente.id)
    else:
        form = HistoriaClinicaOdontologicaForm(instance=historia)
    
    context = {
        'form': form,
        'paciente': paciente,
        'historia': historia if not created else None,
    }
    
    return render(request, 'evolucion/form_historia_clinica.html', context)


@login_required
def detalle_historia_clinica(request, paciente_id):
    """
    Ver detalle de historia clínica.
    """
    if not hasattr(request.user, 'clinica'):
        return redirect('home')
    
    clinica = request.user.clinica
    
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica=clinica)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('home')
    
    try:
        historia = paciente.historia_clinica_odontologica
    except:
        historia = None
    
    # Obtener evoluciones del paciente
    resumen = services.obtener_resumen_paciente(paciente.id, clinica.id)
    
    context = {
        'paciente': paciente,
        'historia': historia,
        'resumen': resumen,
    }
    
    return render(request, 'evolucion/detalle_historia_clinica.html', context)
