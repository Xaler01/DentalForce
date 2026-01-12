"""
Servicios de negocio para evolución odontológica.
"""
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from evolucion.models import (
    EvolucionConsulta,
    ProcedimientoEnEvolucion,
    PlanTratamiento,
    ProcedimientoEnPlan,
    Odontograma,
)
from pacientes.models import Paciente


def evoluciones_para_clinica(clinica_id):
    """
    Obtiene todas las evoluciones de la clínica.
    """
    return EvolucionConsulta.objects.filter(
        paciente__clinica_id=clinica_id
    ).select_related('paciente', 'dentista', 'cita').prefetch_related(
        'procedimientos'
    )


def obtener_evolucion_para_clinica(pk, clinica_id):
    """
    Obtiene una evolución específica con validación de clínica.
    """
    try:
        evolucion = EvolucionConsulta.objects.get(pk=pk)
        if evolucion.paciente.clinica_id != clinica_id:
            return None
        return evolucion
    except EvolucionConsulta.DoesNotExist:
        return None


def crear_evolucion_para_paciente(paciente_id, clinica_id, datos):
    """
    Crea una nueva evolución para un paciente.
    Valida que el paciente pertenezca a la clínica.
    """
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica_id=clinica_id)
    except Paciente.DoesNotExist:
        return None
    
    with transaction.atomic():
        evolucion = EvolucionConsulta.objects.create(
            paciente=paciente,
            fecha_consulta=datos['fecha_consulta'],
            cita=datos.get('cita'),
            dentista=datos.get('dentista'),
            motivo_consulta=datos['motivo_consulta'],
            hallazgos_clinicos=datos.get('hallazgos_clinicos', ''),
            recomendaciones=datos.get('recomendaciones', ''),
            cambios_odontograma=datos.get('cambios_odontograma', ''),
            fecha_proximo_control=datos.get('fecha_proximo_control'),
            uc_id=datos['usuario_id'],
        )
        return evolucion


def agregar_procedimiento_a_evolucion(evolucion_id, clinica_id, procedimiento_id, cantidad=1, observaciones=''):
    """
    Agrega un procedimiento a una evolución.
    """
    try:
        evolucion = EvolucionConsulta.objects.get(pk=evolucion_id)
        if evolucion.paciente.clinica_id != clinica_id:
            return None
    except EvolucionConsulta.DoesNotExist:
        return None
    
    from procedimientos.models import ProcedimientoOdontologico
    
    try:
        procedimiento = ProcedimientoOdontologico.objects.get(pk=procedimiento_id)
    except ProcedimientoOdontologico.DoesNotExist:
        return None
    
    proc_evolucion, created = ProcedimientoEnEvolucion.objects.get_or_create(
        evolucion=evolucion,
        procedimiento=procedimiento,
        defaults={'cantidad': cantidad, 'observaciones': observaciones}
    )
    
    if not created:
        proc_evolucion.cantidad = cantidad
        proc_evolucion.observaciones = observaciones
        proc_evolucion.save()
    
    return proc_evolucion


def eliminar_procedimiento_de_evolucion(evolucion_id, clinica_id, procedimiento_id):
    """
    Elimina un procedimiento de una evolución.
    """
    try:
        evolucion = EvolucionConsulta.objects.get(pk=evolucion_id)
        if evolucion.paciente.clinica_id != clinica_id:
            return False
    except EvolucionConsulta.DoesNotExist:
        return False
    
    deleted, _ = ProcedimientoEnEvolucion.objects.filter(
        evolucion=evolucion,
        procedimiento_id=procedimiento_id
    ).delete()
    
    return deleted > 0


def obtener_evoluciones_paciente(paciente_id, clinica_id):
    """
    Obtiene todas las evoluciones de un paciente.
    """
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica_id=clinica_id)
    except Paciente.DoesNotExist:
        return None
    
    return paciente.evoluciones.all().order_by('-fecha_consulta').prefetch_related(
        'procedimientos'
    )


def planes_tratamiento_para_clinica(clinica_id):
    """
    Obtiene todos los planes de tratamiento de la clínica.
    """
    return PlanTratamiento.objects.filter(
        paciente__clinica_id=clinica_id
    ).select_related('paciente').prefetch_related('procedimientos')


def obtener_plan_para_clinica(pk, clinica_id):
    """
    Obtiene un plan de tratamiento con validación de clínica.
    """
    try:
        plan = PlanTratamiento.objects.get(pk=pk)
        if plan.paciente.clinica_id != clinica_id:
            return None
        return plan
    except PlanTratamiento.DoesNotExist:
        return None


def crear_plan_tratamiento(paciente_id, clinica_id, datos, usuario_id):
    """
    Crea un nuevo plan de tratamiento para un paciente.
    """
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica_id=clinica_id)
    except Paciente.DoesNotExist:
        return None
    
    with transaction.atomic():
        plan = PlanTratamiento.objects.create(
            paciente=paciente,
            nombre=datos['nombre'],
            descripcion=datos.get('descripcion', ''),
            estado=datos.get('estado', 'PENDIENTE'),
            prioridad=datos.get('prioridad', 'NECESARIO'),
            fecha_inicio=datos.get('fecha_inicio'),
            fecha_estimada_fin=datos.get('fecha_estimada_fin'),
            presupuesto_estimado=datos['presupuesto_estimado'],
            uc_id=usuario_id,
        )
        return plan


def agregar_procedimiento_a_plan(plan_id, clinica_id, procedimiento_id, orden=0, precio=0, observaciones=''):
    """
    Agrega un procedimiento a un plan de tratamiento.
    """
    try:
        plan = PlanTratamiento.objects.get(pk=plan_id)
        if plan.paciente.clinica_id != clinica_id:
            return None
    except PlanTratamiento.DoesNotExist:
        return None
    
    from procedimientos.models import ProcedimientoOdontologico
    
    try:
        procedimiento = ProcedimientoOdontologico.objects.get(pk=procedimiento_id)
    except ProcedimientoOdontologico.DoesNotExist:
        return None
    
    proc_plan, created = ProcedimientoEnPlan.objects.get_or_create(
        plan=plan,
        procedimiento=procedimiento,
        defaults={
            'orden': orden,
            'precio': precio,
            'observaciones': observaciones,
        }
    )
    
    if not created:
        proc_plan.orden = orden
        proc_plan.precio = precio
        proc_plan.observaciones = observaciones
        proc_plan.save()
    
    return proc_plan


def obtener_kpis_evolucion_clinica(clinica_id):
    """
    Obtiene indicadores clave para la clínica.
    """
    from django.db.models import Count, Q
    
    evoluciones = EvolucionConsulta.objects.filter(
        paciente__clinica_id=clinica_id
    )
    
    planes = PlanTratamiento.objects.filter(
        paciente__clinica_id=clinica_id
    )
    
    # Total de evoluciones en últimos 30 días
    hace_30_dias = timezone.now() - timezone.timedelta(days=30)
    evoluciones_mes = evoluciones.filter(fecha_consulta__gte=hace_30_dias).count()
    
    # Planes completados
    planes_completados = planes.filter(estado='COMPLETADO').count()
    total_planes = planes.count()
    
    # Pacientes con evoluciones
    pacientes_evoluciones = evoluciones.values('paciente').distinct().count()
    
    # Procedimientos más realizados
    procedimientos_frecuentes = (
        ProcedimientoEnEvolucion.objects
        .filter(evolucion__paciente__clinica_id=clinica_id)
        .values('procedimiento__codigo', 'procedimiento__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    return {
        'evoluciones_mes': evoluciones_mes,
        'total_evoluciones': evoluciones.count(),
        'planes_completados': planes_completados,
        'total_planes': total_planes,
        'porcentaje_planes_completados': (planes_completados / total_planes * 100) if total_planes > 0 else 0,
        'pacientes_con_evoluciones': pacientes_evoluciones,
        'procedimientos_frecuentes': list(procedimientos_frecuentes),
    }


def obtener_resumen_paciente(paciente_id, clinica_id):
    """
    Obtiene el resumen de evoluciones y planes de un paciente.
    """
    try:
        paciente = Paciente.objects.get(pk=paciente_id, clinica_id=clinica_id)
    except Paciente.DoesNotExist:
        return None
    
    evoluciones = paciente.evoluciones.all().count()
    planes = paciente.planes_tratamiento.all().count()
    
    # Última evolución
    ultima_evolucion = paciente.evoluciones.latest('fecha_consulta') if evoluciones > 0 else None
    
    # Planes activos
    planes_activos = paciente.planes_tratamiento.filter(estado='ACTIVO').count()
    
    # Próxima cita según última evolución
    proxima_cita = None
    if ultima_evolucion and ultima_evolucion.fecha_proximo_control:
        proxima_cita = ultima_evolucion.fecha_proximo_control
    
    return {
        'total_evoluciones': evoluciones,
        'total_planes': planes,
        'ultima_evolucion': ultima_evolucion,
        'planes_activos': planes_activos,
        'proxima_cita': proxima_cita,
    }
