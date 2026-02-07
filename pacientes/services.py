from typing import Optional

from django.db.models import QuerySet

from core.services.tenants import get_clinica_from_request
from .models import Paciente
from clinicas.models import Clinica


def pacientes_para_clinica(clinica: Clinica, incluir_inactivos: bool = False) -> QuerySet[Paciente]:
    """Base queryset de pacientes para una clínica.
    - Si `incluir_inactivos` es True: incluye pacientes con `estado=False`
    - Caso contrario: solo activos.
    """
    if incluir_inactivos:
        return Paciente.objects.filter(clinica=clinica)
    return Paciente.objects.para_clinica(clinica.id)


def get_paciente_para_clinica(pk: int, clinica: Clinica) -> Optional[Paciente]:
    """Obtiene un paciente por pk verificado contra la clínica activa."""
    return Paciente.objects.filter(id=pk, clinica=clinica, estado=True).first()


def base_queryset_para_request(request) -> QuerySet[Paciente]:
    """Conveniencia: retorna queryset base para la clínica en la request."""
    clinica = get_clinica_from_request(request)
    if not clinica:
        return Paciente.objects.none()
    return Paciente.objects.filter(clinica=clinica)
