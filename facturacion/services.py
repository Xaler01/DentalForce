"""
Servicios de Facturación - Funciones tenant-aware

Este módulo proporciona servicios para la gestión de facturación
con soporte completo para multi-tenancy. Todas las funciones
validan que el usuario tenga acceso a la clínica especificada.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Factura, ItemFactura, Pago
from pacientes.models import Paciente
from clinicas.models import Clinica
from procedimientos.models import ProcedimientoOdontologico


def facturas_para_clinica(clinica_id):
    """
    Obtiene todas las facturas de una clínica específica
    
    Args:
        clinica_id: ID de la clínica
        
    Returns:
        QuerySet de facturas filtradas por clínica
    """
    return Factura.objects.para_clinica(clinica_id)


def get_factura_para_clinica(pk, clinica_id):
    """
    Obtiene una factura específica validando que pertenezca a la clínica
    
    Args:
        pk: ID de la factura
        clinica_id: ID de la clínica
        
    Returns:
        Objeto Factura si existe y pertenece a la clínica
        
    Raises:
        Factura.DoesNotExist: Si no existe o no pertenece a la clínica
    """
    return Factura.objects.para_clinica(clinica_id).get(pk=pk)


def facturas_pendientes_clinica(clinica_id):
    """
    Obtiene todas las facturas pendientes de pago de una clínica
    
    Args:
        clinica_id: ID de la clínica
        
    Returns:
        QuerySet de facturas pendientes
    """
    return Factura.objects.para_clinica(clinica_id).pendientes()


def facturas_pagadas_clinica(clinica_id):
    """
    Obtiene todas las facturas pagadas de una clínica
    
    Args:
        clinica_id: ID de la clínica
        
    Returns:
        QuerySet de facturas pagadas
    """
    return Factura.objects.para_clinica(clinica_id).pagadas()


def crear_factura_para_paciente(paciente_id, clinica_id, items_data, 
                                cita_id=None, descuento=Decimal('0.00'),
                                observaciones=''):
    """
    Crea una nueva factura para un paciente
    
    Args:
        paciente_id: ID del paciente
        clinica_id: ID de la clínica
        items_data: Lista de dicts con estructura:
            [
                {
                    'procedimiento_id': int,
                    'cantidad': int,
                    'precio_unitario': Decimal,
                    'descuento_item': Decimal (opcional),
                    'descripcion': str (opcional)
                },
                ...
            ]
        cita_id: ID de cita relacionada (opcional)
        descuento: Descuento total de factura (opcional)
        observaciones: Notas sobre la factura (opcional)
        
    Returns:
        Objeto Factura creado
        
    Raises:
        Paciente.DoesNotExist: Si el paciente no existe
        Clinica.DoesNotExist: Si la clínica no existe
        ValueError: Si el paciente no pertenece a la clínica
    """
    # Validar paciente y clínica
    paciente = Paciente.objects.get(pk=paciente_id)
    clinica = Clinica.objects.get(pk=clinica_id)
    
    if paciente.clinica_id != clinica.id:
        raise ValueError(
            f"El paciente {paciente} no pertenece a la clínica {clinica}"
        )
    
    # Validar que existan todos los procedimientos
    procedimientos_ids = [item['procedimiento_id'] for item in items_data]
    procedimientos = ProcedimientoOdontologico.objects.filter(
        pk__in=procedimientos_ids
    )
    
    if procedimientos.count() != len(set(procedimientos_ids)):
        raise ValueError("Uno o más procedimientos no existen")
    
    # Crear factura
    with transaction.atomic():
        factura = Factura.objects.create(
            paciente=paciente,
            clinica=clinica,
            cita_id=cita_id,
            descuento=descuento,
            observaciones=observaciones,
            estado=Factura.ESTADO_PENDIENTE
        )
        
        # Crear ítems
        for item_data in items_data:
            procedimiento = ProcedimientoOdontologico.objects.get(
                pk=item_data['procedimiento_id']
            )
            
            ItemFactura.objects.create(
                factura=factura,
                procedimiento=procedimiento,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario'],
                descuento_item=item_data.get('descuento_item', Decimal('0.00')),
                descripcion=item_data.get('descripcion', ''),
                total=Decimal('0.00')  # Se calcula en save()
            )
        
        # Recalcular totales
        factura.calcular_totales()
    
    return factura


def registrar_pago(factura_id, clinica_id, usuario, monto, forma_pago, 
                   referencia='', observaciones=''):
    """
    Registra un pago contra una factura
    
    Args:
        factura_id: ID de la factura
        clinica_id: ID de la clínica (para validación)
        usuario: Usuario que registra el pago (para auditoría)
        monto: Monto a pagar
        forma_pago: Forma de pago (EFE, TAR, TRA, CHE, SEG, OTR)
        referencia: Referencia del pago (opcional)
        observaciones: Notas sobre el pago (opcional)
        
    Returns:
        Objeto Pago creado
        
    Raises:
        Factura.DoesNotExist: Si la factura no existe
        ValueError: Si la factura no pertenece a la clínica
    """
    factura = get_factura_para_clinica(factura_id, clinica_id)
    
    pago = Pago.objects.create(
        factura=factura,
        monto=monto,
        forma_pago=forma_pago,
        referencia_pago=referencia,
        observaciones=observaciones,
        fecha_pago=timezone.now().date(),
        uc=usuario
    )
    
    return pago


def obtener_saldo_pendiente(factura_id, clinica_id):
    """
    Obtiene el saldo pendiente de una factura
    
    Args:
        factura_id: ID de la factura
        clinica_id: ID de la clínica (para validación)
        
    Returns:
        Decimal con el saldo pendiente
    """
    factura = get_factura_para_clinica(factura_id, clinica_id)
    
    total_pagado = sum(
        (pago.monto for pago in factura.pagos.all()),
        Decimal('0.00')
    )
    
    return factura.total - total_pagado


def obtener_ingresos_clinica(clinica_id, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene los ingresos totales de una clínica en un período
    
    Args:
        clinica_id: ID de la clínica
        fecha_inicio: Fecha de inicio (opcional, por defecto mes actual)
        fecha_fin: Fecha de fin (opcional, por defecto hoy)
        
    Returns:
        Dict con estadísticas de ingresos
    """
    from django.db.models import Sum
    from datetime import date
    
    # Si no se especifican fechas, usar el mes actual
    if not fecha_inicio:
        today = date.today()
        fecha_inicio = date(today.year, today.month, 1)
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    
    # Obtener facturas del período (excluyendo anuladas)
    facturas = Factura.objects.para_clinica(clinica_id).filter(
        fecha_emision__gte=fecha_inicio,
        fecha_emision__lte=fecha_fin
    ).exclude(estado=Factura.ESTADO_ANULADA)
    
    # Calcular totales
    ingresos_totales = facturas.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    # Obtener pagos realizados (suma de todos los pagos en el período)
    from .models import Pago
    pagos_realizados = Pago.objects.filter(
        factura__in=facturas
    ).aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    # Facturas pagadas (estado PAG)
    facturas_pagadas = facturas.filter(estado=Factura.ESTADO_PAGADA)
    facturas_pendientes = facturas.filter(estado=Factura.ESTADO_PENDIENTE)
    
    # Cuentas por cobrar
    cuentas_por_cobrar = ingresos_totales - pagos_realizados
    
    # Calcular tasas
    tasa_cobranza = ((pagos_realizados / ingresos_totales) * 100) if ingresos_totales > 0 else Decimal('0.00')
    tasa_pagadas = ((sum(f.total for f in facturas_pagadas) / ingresos_totales) * 100) if ingresos_totales > 0 else Decimal('0.00')
    tasa_pendientes = ((sum(f.total for f in facturas_pendientes) / ingresos_totales) * 100) if ingresos_totales > 0 else Decimal('0.00')
    
    # Distribución por formas de pago
    formas_pago_stats = {}
    for forma_codigo, forma_nombre in Pago.FORMAS_PAGO_CHOICES:
        monto = Pago.objects.filter(
            factura__in=facturas,
            forma_pago=forma_codigo
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        if monto > 0:
            formas_pago_stats[forma_nombre] = float(monto)
    
    return {
        'periodo_inicio': fecha_inicio,
        'periodo_fin': fecha_fin,
        'facturas_emitidas': facturas.count(),
        'facturas_pagadas': facturas_pagadas.count(),
        'facturas_pendientes': facturas_pendientes.count(),
        # Compatibilidad con template (usar "ingresos" y "total_pagado")
        'ingresos': ingresos_totales,
        'ingresos_totales': ingresos_totales,
        'total_pagado': pagos_realizados,
        'pagos_realizados': pagos_realizados,
        'total_pendiente': cuentas_por_cobrar,
        'cuentas_por_cobrar': cuentas_por_cobrar,
        # Tasas
        'tasa_cobranza': tasa_cobranza,
        'tasa_pagadas': tasa_pagadas,
        'tasa_pendientes': tasa_pendientes,
        # Distribuciones para gráficos
        'formas_pago_stats': formas_pago_stats,
    }


def obtener_resumen_paciente(paciente_id, clinica_id):
    """
    Obtiene un resumen de facturación de un paciente
    
    Args:
        paciente_id: ID del paciente
        clinica_id: ID de la clínica
        
    Returns:
        Dict con resumen de facturación
    """
    from django.db.models import Sum, Count
    
    # Validar que paciente pertenezca a clínica
    paciente = Paciente.objects.get(pk=paciente_id)
    if paciente.clinica_id != clinica_id:
        raise ValueError(
            f"El paciente {paciente} no pertenece a la clínica {clinica_id}"
        )
    
    facturas = Factura.objects.para_clinica(clinica_id).filter(
        paciente=paciente
    )
    
    total_gastado = facturas.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')
    
    total_pagado = Pago.objects.filter(
        factura__paciente=paciente
    ).aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')
    
    return {
        'paciente': paciente,
        'total_facturas': facturas.count(),
        'facturas_pagadas': facturas.filter(
            estado=Factura.ESTADO_PAGADA
        ).count(),
        'facturas_pendientes': facturas.filter(
            estado=Factura.ESTADO_PENDIENTE
        ).count(),
        'total_gastado': total_gastado,
        'total_pagado': total_pagado,
        'saldo_pendiente': total_gastado - total_pagado,
    }


