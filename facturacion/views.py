"""
Vistas para el módulo de Facturación

Este módulo contiene las vistas para gestión de facturas con soporte
completo para multi-tenancy y validación de permisos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Factura, ItemFactura, Pago
from .forms import FacturaForm, ItemFacturaForm, PagoForm, BuscarFacturaForm
from . import services
from pacientes.models import Paciente
from clinicas.models import Clinica
from core.services.tenants import get_clinica_from_request


@login_required
def lista_facturas(request):
    """
    Lista todas las facturas de la clínica activa del usuario
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    # Formulario de búsqueda
    form = BuscarFacturaForm(request.GET, clinica=clinica)
    
    # Obtener facturas de la clínica
    facturas = services.facturas_para_clinica(clinica.id)
    
    # Aplicar filtros si el formulario es válido
    if form.is_valid():
        numero = form.cleaned_data.get('numero_factura')
        paciente = form.cleaned_data.get('paciente')
        estado = form.cleaned_data.get('estado')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        
        if numero:
            facturas = facturas.filter(numero_factura__icontains=numero)
        
        if paciente:
            facturas = facturas.filter(paciente=paciente)
        
        if estado:
            facturas = facturas.filter(estado=estado)
        
        if fecha_desde:
            facturas = facturas.filter(fecha_emision__gte=fecha_desde)
        
        if fecha_hasta:
            facturas = facturas.filter(fecha_emision__lte=fecha_hasta)
    
    # Ordenar por fecha más reciente
    facturas = facturas.order_by('-fecha_emision', '-id')
    
    # Calcular totales (EXCLUYENDO facturas anuladas)
    facturas_activas = facturas.exclude(estado='ANU')
    total_facturas = facturas.count()
    total_monto = sum(f.total for f in facturas_activas)
    total_pagado = sum(f.total_pagado for f in facturas_activas)
    total_pendiente = total_monto - total_pagado
    
    context = {
        'facturas': facturas,
        'form': form,
        'clinica': clinica,
        'total_facturas': total_facturas,
        'total_monto': total_monto,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
    }
    
    return render(request, 'facturacion/lista_facturas.html', context)


@login_required
def detalle_factura(request, pk):
    """
    Muestra el detalle de una factura específica
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    # Obtener factura validando que pertenece a la clínica
    factura = services.get_factura_para_clinica(pk, clinica.id)
    
    if not factura:
        messages.error(request, "Factura no encontrada o no tiene acceso")
        return redirect('facturacion:lista')
    
    # Obtener items y pagos
    items = factura.items.all()
    pagos = factura.pagos.all().order_by('-fecha_pago')
    
    context = {
        'factura': factura,
        'items': items,
        'pagos': pagos,
        'clinica': clinica,
    }
    
    return render(request, 'facturacion/detalle_factura.html', context)


@login_required
def nueva_factura(request):
    """
    Crea una nueva factura para la clínica
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    if request.method == 'POST':
        form = FacturaForm(request.POST, clinica=clinica)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear factura
                    factura = form.save(commit=False)
                    factura.clinica = clinica
                    factura.uc = request.user
                    factura.save()
                    
                    messages.success(
                        request,
                        f"Factura {factura.numero_factura} creada exitosamente"
                    )
                    
                    return redirect('facturacion:editar_items', pk=factura.pk)
            
            except Exception as e:
                messages.error(request, f"Error al crear factura: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            # Log de errores de formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = FacturaForm(clinica=clinica)
    
    context = {
        'form': form,
        'clinica': clinica,
        'titulo': 'Nueva Factura',
    }
    
    return render(request, 'facturacion/form_factura.html', context)


@login_required
def editar_items_factura(request, pk):
    """
    Permite agregar/editar items de una factura
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    factura = services.get_factura_para_clinica(pk, clinica.id)
    
    if not factura:
        messages.error(request, "Factura no encontrada")
        return redirect('facturacion:lista')
    
    # Solo permitir editar facturas pendientes
    if factura.estado != Factura.ESTADO_PENDIENTE:
        messages.warning(request, "Solo se pueden editar facturas pendientes")
        return redirect('facturacion:detalle', pk=pk)
    
    if request.method == 'POST':
        form = ItemFacturaForm(request.POST, factura=factura)
        
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.factura = factura
                item.uc = request.user
                item.save()
                
                # Recalcular totales
                factura.calcular_totales()
                
                messages.success(request, "Item agregado exitosamente")
                return redirect('facturacion:editar_items', pk=pk)
            
            except Exception as e:
                messages.error(request, f"Error al agregar item: {str(e)}")
    else:
        form = ItemFacturaForm(factura=factura)
    
    items = factura.items.all()
    
    context = {
        'factura': factura,
        'items': items,
        'form': form,
        'clinica': clinica,
    }
    
    return render(request, 'facturacion/editar_items.html', context)


@login_required
def eliminar_item_factura(request, factura_pk, item_pk):
    """
    Elimina un item de la factura
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        return JsonResponse({'error': 'Usuario sin clínica'}, status=403)
    
    factura = services.get_factura_para_clinica(factura_pk, clinica.id)
    
    if not factura:
        return JsonResponse({'error': 'Factura no encontrada'}, status=404)
    
    if factura.estado != Factura.ESTADO_PENDIENTE:
        return JsonResponse({'error': 'Solo se pueden editar facturas pendientes'}, status=403)
    
    try:
        item = ItemFactura.objects.get(pk=item_pk, factura=factura)
        item.delete()
        
        # Recalcular totales
        factura.calcular_totales()
        
        return JsonResponse({
            'success': True,
            'subtotal': float(factura.subtotal),
            'iva_monto': float(factura.iva_monto),
            'total': float(factura.total)
        })
    
    except ItemFactura.DoesNotExist:
        return JsonResponse({'error': 'Item no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def registrar_pago(request, pk):
    """
    Registra un pago para una factura
    """
    import logging
    logger = logging.getLogger('facturacion')
    
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    factura = services.get_factura_para_clinica(pk, clinica.id)
    
    if not factura:
        messages.error(request, "Factura no encontrada")
        return redirect('facturacion:lista')
    
    # No permitir pagos en facturas anuladas
    if factura.estado == Factura.ESTADO_ANULADA:
        messages.error(request, "No se pueden registrar pagos en facturas anuladas")
        return redirect('facturacion:detalle', pk=pk)
    
    if request.method == 'POST':
        form = PagoForm(request.POST, factura=factura)
        
        if form.is_valid():
            try:
                logger.info(f"Registrando pago para factura {factura.id}: ${form.cleaned_data['monto']}")
                
                # Usar el servicio para registrar el pago, pasando el usuario
                pago = services.registrar_pago(
                    factura_id=factura.id,
                    clinica_id=clinica.id,
                    usuario=request.user,
                    monto=form.cleaned_data['monto'],
                    forma_pago=form.cleaned_data['forma_pago'],
                    referencia=form.cleaned_data.get('referencia_pago', ''),
                    observaciones=form.cleaned_data.get('observaciones', '')
                )
                
                logger.info(f"Pago registrado exitosamente: {pago.id} - ${pago.monto}")
                
                messages.success(request, f"Pago de ${pago.monto:.2f} registrado exitosamente")
                return redirect('facturacion:detalle', pk=pk)
            
            except Exception as e:
                messages.error(request, f"Error al registrar pago: {str(e)}")
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PagoForm(factura=factura)
    
    pagos = factura.pagos.all().order_by('-fecha_pago')
    
    context = {
        'factura': factura,
        'form': form,
        'pagos': pagos,
        'clinica': clinica,
        'saldo_pendiente': factura.total - factura.total_pagado,
    }
    
    return render(request, 'facturacion/registrar_pago.html', context)


@login_required
def anular_factura(request, pk):
    """
    Anula una factura
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "Usuario sin clínica")
        return redirect('clinicas:seleccionar')
    
    factura = services.get_factura_para_clinica(pk, clinica.id)
    
    if not factura:
        messages.error(request, "Factura no encontrada")
        return redirect('facturacion:lista')
    
    # Solo permitir anular facturas pendientes
    if factura.estado != Factura.ESTADO_PENDIENTE:
        messages.error(request, "Solo se pueden anular facturas pendientes")
        return redirect('facturacion:detalle', pk=pk)
    
    if request.method == 'POST':
        try:
            factura.estado = Factura.ESTADO_ANULADA
            factura.save(update_fields=['estado', 'fm'])
            
            messages.success(request, f"Factura {factura.numero_factura} anulada exitosamente")
            return redirect('facturacion:detalle', pk=pk)
        
        except Exception as e:
            messages.error(request, f"Error al anular factura: {str(e)}")
            return redirect('facturacion:detalle', pk=pk)
    
    # Si es GET, mostrar confirmación
    return redirect('facturacion:detalle', pk=pk)


@login_required
def imprimir_factura(request, pk):
    """
    Vista dedicada para imprimir factura con nombre personalizado
    """
    from datetime import datetime
    
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    factura = services.get_factura_para_clinica(pk, clinica.id)
    
    if not factura:
        messages.error(request, "Factura no encontrada")
        return redirect('facturacion:lista')
    
    # Obtener pagos
    pagos = []
    total_pagado = Decimal('0.00')
    
    if factura.estado in [Factura.ESTADO_PENDIENTE, Factura.ESTADO_PAGADA]:
        pagos = factura.pagos.all().order_by('-fecha_pago')
        total_pagado = factura.total_pagado
    
    # Nombre del archivo PDF
    fecha_impresion = datetime.now().strftime('%Y%m%d')
    nombre_paciente = f"{factura.paciente.apellidos}_{factura.paciente.nombres}".replace(' ', '_')
    nombre_archivo = f"{factura.numero_factura}_{nombre_paciente}_{fecha_impresion}.pdf"
    
    context = {
        'factura': factura,
        'clinica': clinica,
        'items': factura.items.all(),
        'pagos': pagos,
        'total_pagado': total_pagado,
        'saldo_pendiente': factura.total - total_pagado,
        'nombre_archivo': nombre_archivo,
    }
    
    response = render(request, 'facturacion/imprimir_factura.html', context)
    
    # Agregar header para sugerir nombre de archivo al imprimir
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    
    return response


@login_required
def reporte_facturas(request):
    """
    Genera reportes de facturación
    """
    clinica = get_clinica_from_request(request)
    
    if not clinica:
        messages.error(request, "No tiene clínica seleccionada")
        return redirect('clinicas:seleccionar')
    
    # Obtener parámetros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Por defecto: desde HOY hasta HOY (para reporte diario)
    if not fecha_desde:
        fecha_desde = datetime.now().strftime('%Y-%m-%d')
    
    if not fecha_hasta:
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
    
    # Usar el servicio para obtener ingresos
    resumen = services.obtener_ingresos_clinica(
        clinica_id=clinica.id,
        fecha_inicio=fecha_desde,
        fecha_fin=fecha_hasta
    )
    
    context = {
        'clinica': clinica,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'resumen': resumen,
    }
    
    return render(request, 'facturacion/reporte_facturas.html', context)


@login_required
def obtener_citas_paciente(request):
    """
    Retorna las citas de un paciente en formato JSON para AJAX
    Usado para filtrar citas dinámicamente en el formulario de factura
    """
    try:
        clinica = get_clinica_from_request(request)
        paciente_id = request.GET.get('paciente_id')
        
        if not clinica or not paciente_id:
            return JsonResponse({'error': 'Parámetros inválidos', 'citas': []})
        
        from cit.models import Cita
        from pacientes.models import Paciente
        
        # Primero validar que el paciente existe y pertenece a la clínica
        try:
            paciente = Paciente.objects.get(id=paciente_id, clinica=clinica)
        except Paciente.DoesNotExist:
            return JsonResponse({'error': 'Paciente no encontrado', 'citas': []})
        
        # Obtener citas del paciente
        # Solo mostrar citas que no están canceladas o no asistidas
        citas = Cita.objects.filter(
            paciente=paciente
        ).exclude(
            estado__in=['CAN', 'NAS']  # Excluir canceladas y no asistidas
        ).order_by('-fecha_hora').values('id', 'fecha_hora', 'estado')
        
        # Limitar a últimas 20 citas
        citas_list = []
        for cita in citas[:20]:
            fecha_hora = cita['fecha_hora']
            citas_list.append({
                'id': cita['id'],
                'numero_cita': f"#{cita['id']}",
                'fecha_hora': fecha_hora.strftime('%Y-%m-%d %H:%M'),
                'fecha_hora_display': fecha_hora.strftime('%d/%m/%Y %H:%M'),
                'estado': cita['estado']
            })
        
        return JsonResponse({'citas': citas_list, 'success': True})
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return JsonResponse({'error': error_msg, 'citas': [], 'success': False})
