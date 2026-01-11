from typing import Optional

from django.http import HttpRequest

from clinicas.models import Clinica


def get_clinica_from_request(request: HttpRequest) -> Optional[Clinica]:
    """Obtiene la clínica activa desde la sesión o None si no existe.

    No aplica fallback por seguridad multi-tenant. Debe existir `clinica_id` en sesión
    o el middleware redirige al selector.
    """
    try:
        clinica_id = request.session.get('clinica_id')
    except Exception:
        clinica_id = None

    if not clinica_id:
        return None

    return Clinica.objects.filter(id=clinica_id, estado=True).first()
