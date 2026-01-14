"""
Señales para el módulo de Evolución

Gestiona la creación automática de ServicioPendiente cuando
un odontólogo registra procedimientos realizados en evoluciones.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProcedimientoEnEvolucion


@receiver(post_save, sender=ProcedimientoEnEvolucion)
def crear_servicio_pendiente(sender, instance, created, **kwargs):
    """
    Cuando se crea un ProcedimientoEnEvolucion, automáticamente
    crea o actualiza un ServicioPendiente en facturación.
    
    Esto permite que el administrativo solo pueda facturar
    los tratamientos que el odontólogo realmente realizó.
    """
    # Importación lazy para evitar circular imports
    from facturacion.models import ServicioPendiente
    
    # Solo procesar en creación (no en actualización)
    if created:
        # Obtener clínica del paciente
        clinica = instance.evolucion.paciente.clinica
        
        # Buscar si ya existe un ServicioPendiente del mismo procedimiento
        # que esté pendiente o parcialmente facturado
        servicio_existente = ServicioPendiente.objects.filter(
            paciente=instance.evolucion.paciente,
            procedimiento=instance.procedimiento,
            dentista=instance.evolucion.dentista,
            fecha_realizacion=instance.evolucion.fecha_consulta
        ).exclude(
            estado=ServicioPendiente.ESTADO_ANULADO
        ).first()
        
        if servicio_existente:
            # Si existe, actualizar cantidad realizada
            servicio_existente.cantidad_realizada += instance.cantidad
            servicio_existente.descripcion = f"{servicio_existente.descripcion} | +{instance.cantidad} unidad(es) - {instance.evolucion.fecha_consulta}"
            servicio_existente.actualizar_estado()
            servicio_existente.save()
        else:
            # Si no existe, crear uno nuevo
            ServicioPendiente.objects.create(
                paciente=instance.evolucion.paciente,
                clinica=clinica,
                dentista=instance.evolucion.dentista,
                procedimiento=instance.procedimiento,
                fecha_realizacion=instance.evolucion.fecha_consulta,
                cantidad_realizada=instance.cantidad,
                cantidad_facturada=0,
                descripcion=f"Procedimiento realizado en consulta del {instance.evolucion.fecha_consulta}",
                estado=ServicioPendiente.ESTADO_PENDIENTE,
                uc=instance.uc
            )


@receiver(post_delete, sender=ProcedimientoEnEvolucion)
def eliminar_servicio_pendiente(sender, instance, **kwargs):
    """
    Cuando se elimina un ProcedimientoEnEvolucion, actualiza o elimina
    el ServicioPendiente correspondiente.
    
    IMPORTANTE: Solo permite eliminación si NO ha sido facturado aún.
    """
    from facturacion.models import ServicioPendiente
    
    # Buscar el servicio pendiente correspondiente
    servicios = ServicioPendiente.objects.filter(
        paciente=instance.evolucion.paciente,
        procedimiento=instance.procedimiento,
        fecha_realizacion=instance.evolucion.fecha_consulta
    ).exclude(
        estado=ServicioPendiente.ESTADO_ANULADO
    )
    
    for servicio in servicios:
        # Solo permitir eliminación si NO ha sido facturado
        if servicio.cantidad_facturada == 0:
            # Si no se ha facturado nada, se puede eliminar
            if servicio.cantidad_realizada == instance.cantidad:
                # Es exactamente el mismo, eliminar
                servicio.delete()
            else:
                # Hay más unidades registradas, solo restar
                servicio.cantidad_realizada -= instance.cantidad
                if servicio.cantidad_realizada < servicio.cantidad_facturada:
                    servicio.cantidad_realizada = servicio.cantidad_facturada
                servicio.actualizar_estado()
                servicio.save()
        else:
            # Ya hay facturación, solo ajustar si es posible
            nueva_cantidad = servicio.cantidad_realizada - instance.cantidad
            if nueva_cantidad >= servicio.cantidad_facturada:
                servicio.cantidad_realizada = nueva_cantidad
                servicio.actualizar_estado()
                servicio.save()
            # Si nueva_cantidad < facturada, no se puede eliminar
            # (esto debería bloquearse desde el formulario/vista)
