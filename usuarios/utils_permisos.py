"""Helpers para mapear permisos Django a permisos granulares de PowerDent."""
from typing import Iterable, Optional
from django.contrib.auth.models import User


# Mapeo simple de permisos de modelos Django a códigos granulares
# Se usa para compatibilidad con vistas legacy que siguen usando PermissionRequiredMixin.

def _mapear_codigo_granular(codigo_django: str) -> Optional[str]:
    if codigo_django.startswith('inv.'):
        # Operaciones de catálogo/almacén
        if any(op in codigo_django for op in ('add_', 'change_', 'delete_', 'crear', 'crear', 'nuevo', 'nueva')):
            return 'inventario.solicitar_inventario'
        return 'inventario.ver_inventario'
    if codigo_django.startswith('procedimientos.'):
        # Catálogos clínicos: procedimientos y precios
        return 'admin.gestionar_sucursales'
    if codigo_django.startswith('clinicas.') or codigo_django.startswith('cit.'):
        # Configuración de clínica/sucursales
        return 'admin.gestionar_sucursales'
    return None


def tiene_permiso_granular(user: User, permisos_requeridos) -> bool:
    """Evalúa permisos considerando los códigos granulares del sistema."""
    if user.is_superuser:
        return True

    # Permisos estándar de Django (por si existen en BD)
    if user.has_perms(permisos_requeridos):
        return True

    try:
        uc = user.clinica_asignacion
    except Exception:
        return False

    if isinstance(permisos_requeridos, str):
        permisos = [permisos_requeridos]
    else:
        permisos = list(permisos_requeridos)

    for codigo_django in permisos:
        codigo_granular = _mapear_codigo_granular(codigo_django)
        if not codigo_granular:
            return False
        if not uc.tiene_permiso(codigo_granular):
            return False
    return True
