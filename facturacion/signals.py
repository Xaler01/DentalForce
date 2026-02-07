"""
Señales para el módulo de facturación.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Factura


@receiver(post_save, sender=Factura)
def marcar_cita_completada(sender, instance, created, **kwargs):
    """
    Marca la cita asociada como COMPLETADA cuando se genera una factura con ítems.
    
    SOOD-EVO: Automatización del flujo Evolución → Facturación → Cita Completada
    """
    # Solo procesar si la factura tiene una cita asociada
    if not instance.cita:
        return
    
    # Verificar que la factura tenga ítems
    if not instance.items.exists():
        return
    
    # Importar aquí para evitar importación circular
    from cit.models import Cita
    
    cita = instance.cita
    
    # Solo marcar como completada si no está ya en ese estado
    if cita.estado != Cita.ESTADO_COMPLETADA:
        cita.estado = Cita.ESTADO_COMPLETADA
        cita.save(update_fields=['estado', 'fm'])
