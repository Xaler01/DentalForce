"""Señales automáticas para actualizar alertas de pacientes.
SOOD-80: Actualización automática de alertas al modificar enfermedades o VIP.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from pacientes.models import Paciente
from .models import EnfermedadPaciente
from .utils import GestorAlertas


def _get_usuario(instance):
    """Obtiene el usuario asociado al registro, si existe."""
    return getattr(instance, 'uc', None)


@receiver(post_save, sender=EnfermedadPaciente)
def actualizar_alertas_por_enfermedad(sender, instance, **kwargs):
    """Actualiza alertas cuando se crea/actualiza una EnfermedadPaciente."""
    usuario = _get_usuario(instance)
    GestorAlertas(instance.paciente, usuario).actualizar_alertas()


@receiver(post_delete, sender=EnfermedadPaciente)
def actualizar_alertas_al_eliminar_enfermedad(sender, instance, **kwargs):
    """Actualiza alertas cuando se elimina una EnfermedadPaciente."""
    usuario = _get_usuario(instance)
    GestorAlertas(instance.paciente, usuario).actualizar_alertas()


@receiver(post_save, sender=Paciente)
def actualizar_alertas_por_paciente(sender, instance, **kwargs):
    """Actualiza alertas cuando cambia el paciente (VIP u otros datos relevantes)."""
    usuario = _get_usuario(instance)
    GestorAlertas(instance, usuario).actualizar_alertas()
