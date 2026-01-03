"""
Signals para el modelo Cita y Dentista
"""
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from .models import Cita
from personal.models import Dentista


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


@receiver(post_save, sender=Dentista)
def dentista_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un dentista.
    Asigna automáticamente "Odontología General" y "Diagnóstico" al nuevo dentista.
    """
    if created:
        from django.conf import settings
        # Permitir desactivar la asignación automática (útil para pruebas)
        if not getattr(settings, 'ASSIGN_ESPECIALIDADES_BASE', False):
            return
        try:
            from .models import Especialidad
            # Obtener o crear la especialidad "Odontología General"
            odontologia_general, _ = Especialidad.objects.get_or_create(
                nombre='Odontología General',
                defaults={
                    'descripcion': 'Odontología General - Servicios básicos de odontología, resinas y tratamientos de emergencia',
                    'duracion_default': 30,
                    'color_calendario': '#2ecc71',  # Verde
                    'estado': True,
                    'uc': instance.uc,
                    'um': instance.um,
                }
            )

            # Obtener o crear la especialidad "Diagnóstico"
            diagnostico, _ = Especialidad.objects.get_or_create(
                nombre='Diagnóstico',
                defaults={
                    'descripcion': 'Evaluación diagnóstica inicial y seguimiento clínico',
                    'duracion_default': 30,
                    'color_calendario': '#8e44ad',  # Morado
                    'estado': True,
                    'uc': instance.uc,
                    'um': instance.um,
                }
            )

            # Asignar especialidades obligatorias al dentista si no las tiene
            for esp in (odontologia_general, diagnostico):
                if not instance.especialidades.filter(pk=esp.pk).exists():
                    instance.especialidades.add(esp)
        except Exception as e:
            # Evitar que el error en el signal afecte la creación del dentista
            print(f"Error asignando especialidades base al dentista: {e}")
