"""
Servicios para el módulo de Citas (SOOD-CIT-301)
Proporciona funciones tenant-aware para gestión de citas.
"""
from django.db.models import Q
from .models import Cita
from clinicas.models import Clinica


def citas_para_clinica(clinica, estado=None, dentista=None, especialidad=None):
    """
    Retorna citas filtradas por clínica activa.
    
    Args:
        clinica: Instancia de Clinica
        estado: (opcional) Estado de la cita (PEN, CON, etc.)
        dentista: (opcional) Instancia de Dentista para filtro adicional
        especialidad: (opcional) Instancia de Especialidad para filtro adicional
    
    Returns:
        QuerySet de Cita optimizado con select_related
    """
    if not clinica:
        return Cita.objects.none()
    
    # Filtrar por clínica a través de paciente
    qs = Cita.objects.filter(paciente__clinica=clinica).select_related(
        'paciente',
        'dentista',
        'dentista__usuario',
        'especialidad',
        'cubiculo',
        'cubiculo__sucursal'
    )
    
    # Filtros opcionales
    if estado:
        qs = qs.filter(estado=estado)
    
    if dentista:
        qs = qs.filter(dentista=dentista)
    
    if especialidad:
        qs = qs.filter(especialidad=especialidad)
    
    return qs.order_by('-fecha_hora')


def get_cita_para_clinica(pk, clinica):
    """
    Obtiene una cita específica validando que pertenece a la clínica activa.
    
    Args:
        pk: ID de la cita
        clinica: Instancia de Clinica para validación de acceso
    
    Returns:
        Instancia de Cita o None si no existe o no pertenece a la clínica
    """
    if not clinica:
        return None
    
    try:
        return Cita.objects.filter(
            pk=pk,
            paciente__clinica=clinica
        ).select_related(
            'paciente',
            'dentista',
            'dentista__usuario',
            'especialidad',
            'cubiculo',
            'cubiculo__sucursal'
        ).first()
    except Cita.DoesNotExist:
        return None


def contar_citas_paciente_clinica(paciente, clinica):
    """
    Retorna conteo de citas de un paciente en la clínica especificada.
    
    Args:
        paciente: Instancia de Paciente
        clinica: Instancia de Clinica
    
    Returns:
        int: Número de citas
    """
    if not clinica:
        return 0
    
    return Cita.objects.filter(
        paciente=paciente,
        paciente__clinica=clinica
    ).count()


def citas_proximas_clinica(clinica, dias=7):
    """
    Retorna citas próximas a realizarse en la clínica.
    
    Args:
        clinica: Instancia de Clinica
        dias: Número de días hacia el futuro (default: 7)
    
    Returns:
        QuerySet de Cita ordenado por fecha
    """
    from django.utils import timezone
    from datetime import timedelta
    
    if not clinica:
        return Cita.objects.none()
    
    ahora = timezone.now()
    fecha_limite = ahora + timedelta(days=dias)
    
    return Cita.objects.filter(
        paciente__clinica=clinica,
        fecha_hora__gte=ahora,
        fecha_hora__lte=fecha_limite,
        estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_PENDIENTE]
    ).select_related(
        'paciente',
        'dentista',
        'especialidad',
        'cubiculo'
    ).order_by('fecha_hora')


def citas_por_dentista_clinica(dentista, clinica):
    """
    Retorna todas las citas de un dentista en la clínica especificada.
    
    Args:
        dentista: Instancia de Dentista
        clinica: Instancia de Clinica
    
    Returns:
        QuerySet de Cita del dentista en esa clínica
    """
    if not clinica:
        return Cita.objects.none()
    
    return Cita.objects.filter(
        dentista=dentista,
        paciente__clinica=clinica
    ).select_related(
        'paciente',
        'especialidad',
        'cubiculo'
    ).order_by('-fecha_hora')
