"""
Signals para el modelo Cita
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Cita


@receiver(pre_save, sender=Cita)
def cita_pre_save(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de guardar una cita
    Útil para validaciones adicionales o logging
    """
    # Si la cita ya existía, verificar cambios de estado
    if instance.pk:
        try:
            cita_anterior = Cita.objects.get(pk=instance.pk)
            instance._estado_anterior = cita_anterior.estado
        except Cita.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Cita)
def cita_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar una cita
    Aquí se pueden implementar notificaciones futuras
    """
    # Si es una nueva cita
    if created:
        # TODO: Enviar notificación de creación (email/whatsapp)
        # print(f"Nueva cita creada: {instance}")
        pass
    else:
        # Si cambió el estado
        if hasattr(instance, '_estado_anterior') and instance._estado_anterior:
            if instance._estado_anterior != instance.estado:
                # TODO: Enviar notificación de cambio de estado
                # print(f"Cita {instance.pk} cambió de {instance._estado_anterior} a {instance.estado}")
                
                # Casos específicos por estado
                if instance.estado == Cita.ESTADO_CONFIRMADA:
                    # TODO: Enviar confirmación al paciente
                    pass
                elif instance.estado == Cita.ESTADO_CANCELADA:
                    # TODO: Enviar notificación de cancelación
                    pass
                elif instance.estado == Cita.ESTADO_COMPLETADA:
                    # TODO: Enviar encuesta de satisfacción
                    pass
                elif instance.estado == Cita.ESTADO_NO_ASISTIO:
                    # TODO: Registrar inasistencia en historial del paciente
                    pass
