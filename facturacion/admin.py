from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal
from .models import Factura, ItemFactura, Pago


class ItemFacturaInline(admin.TabularInline):
    """Inline para agregar/editar ítems directamente en la factura"""
    model = ItemFactura
    extra = 1
    fields = ('procedimiento', 'cantidad', 'precio_unitario', 'descuento_item', 'total')
    readonly_fields = ('total',)
    
    def get_queryset(self, request):
        """Filtrar por clínica del usuario"""
        qs = super().get_queryset(request)
        return qs


class PagoInline(admin.TabularInline):
    """Inline para registrar pagos directamente en la factura"""
    model = Pago
    extra = 0
    fields = ('fecha_pago', 'monto', 'forma_pago', 'referencia_pago')
    readonly_fields = ('fc',)
    
    def get_queryset(self, request):
        """Filtrar por clínica del usuario"""
        qs = super().get_queryset(request)
        return qs


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """Admin interface para Facturas"""
    
    list_display = (
        'numero_factura',
        'paciente_link',
        'fecha_emision',
        'total_display',
        'estado_badge',
        'saldo_pendiente_display'
    )
    list_filter = ('estado', 'fecha_emision', 'clinica')
    search_fields = ('numero_factura', 'paciente__nombres', 'paciente__apellidos', 'paciente__cedula')
    readonly_fields = ('numero_factura', 'subtotal', 'iva_monto', 'total', 'fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información de Factura', {
            'fields': ('numero_factura', 'fecha_emision', 'estado')
        }),
        ('Datos del Cliente', {
            'fields': ('paciente', 'clinica', 'sucursal', 'cita')
        }),
        ('Montos', {
            'fields': (
                'subtotal', 'iva_porcentaje', 'iva_monto', 'descuento', 'total'
            )
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ItemFacturaInline, PagoInline]
    
    def paciente_link(self, obj):
        """Mostrar nombre del paciente como link"""
        return f"{obj.paciente.nombres} {obj.paciente.apellidos}"
    paciente_link.short_description = 'Paciente'
    
    def total_display(self, obj):
        """Mostrar total formateado"""
        return f"${obj.total:,.2f}"
    total_display.short_description = 'Total'
    
    def estado_badge(self, obj):
        """Mostrar estado con badge de color"""
        colors = {
            Factura.ESTADO_PENDIENTE: '#ff9800',
            Factura.ESTADO_PAGADA: '#4caf50',
            Factura.ESTADO_ANULADA: '#f44336',
        }
        color = colors.get(obj.estado, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def saldo_pendiente_display(self, obj):
        """Mostrar saldo pendiente"""
        total_pagado = sum(
            (pago.monto for pago in obj.pagos.all()),
            Decimal('0.00')
        )
        saldo = obj.total - total_pagado
        
        if saldo <= 0:
            color = '#4caf50'
            texto = 'Pagada'
        elif saldo == obj.total:
            color = '#ff9800'
            texto = f"${saldo:,.2f}"
        else:
            color = '#ff9800'
            texto = f"${saldo:,.2f}"
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            texto
        )
    saldo_pendiente_display.short_description = 'Saldo Pendiente'
    
    def get_queryset(self, request):
        """Filtrar facturas por clínica del usuario"""
        qs = super().get_queryset(request)
        
        # Si el usuario tiene clinica_seleccionada, filtrar por esa
        if hasattr(request, 'clinica_seleccionada') and request.clinica_seleccionada:
            qs = qs.filter(clinica=request.clinica_seleccionada)
        
        return qs
    
    def save_model(self, request, obj, form, change):
        """Asignar clínica del usuario si no está especificada"""
        if not change and hasattr(request, 'clinica_seleccionada') and request.clinica_seleccionada:
            obj.clinica = request.clinica_seleccionada
        super().save_model(request, obj, form, change)


@admin.register(ItemFactura)
class ItemFacturaAdmin(admin.ModelAdmin):
    """Admin interface para Ítems de Factura"""
    
    list_display = ('factura', 'procedimiento', 'cantidad', 'precio_unitario', 'total_display')
    list_filter = ('factura__fecha_emision', 'procedimiento')
    search_fields = ('factura__numero_factura', 'procedimiento__nombre')
    readonly_fields = ('total', 'fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información', {
            'fields': ('factura', 'procedimiento', 'descripcion')
        }),
        ('Precios', {
            'fields': ('cantidad', 'precio_unitario', 'descuento_item', 'total')
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def total_display(self, obj):
        """Mostrar total formateado"""
        return f"${obj.total:,.2f}"
    total_display.short_description = 'Total'
    
    def get_queryset(self, request):
        """Filtrar por clínica del usuario"""
        qs = super().get_queryset(request)
        
        if hasattr(request, 'clinica_seleccionada') and request.clinica_seleccionada:
            qs = qs.filter(factura__clinica=request.clinica_seleccionada)
        
        return qs


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Admin interface para Pagos"""
    
    list_display = (
        'factura_display',
        'monto_display',
        'fecha_pago',
        'forma_pago_badge',
        'referencia_pago'
    )
    list_filter = ('fecha_pago', 'forma_pago', 'factura__clinica')
    search_fields = ('factura__numero_factura', 'referencia_pago')
    readonly_fields = ('fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información de Pago', {
            'fields': ('factura', 'monto', 'fecha_pago', 'forma_pago')
        }),
        ('Referencia', {
            'fields': ('referencia_pago', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def factura_display(self, obj):
        """Mostrar factura relacionada"""
        return f"{obj.factura.numero_factura} - {obj.factura.paciente}"
    factura_display.short_description = 'Factura'
    
    def monto_display(self, obj):
        """Mostrar monto formateado"""
        return f"${obj.monto:,.2f}"
    monto_display.short_description = 'Monto'
    
    def forma_pago_badge(self, obj):
        """Mostrar forma de pago con badge"""
        colores = {
            Pago.FORMA_EFECTIVO: '#2196f3',
            Pago.FORMA_TARJETA: '#9c27b0',
            Pago.FORMA_TRANSFERENCIA: '#00bcd4',
            Pago.FORMA_CHEQUE: '#ff9800',
            Pago.FORMA_SEGURO: '#4caf50',
            Pago.FORMA_OTRO: '#999999',
        }
        color = colores.get(obj.forma_pago, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_forma_pago_display()
        )
    forma_pago_badge.short_description = 'Forma de Pago'
    
    def get_queryset(self, request):
        """Filtrar por clínica del usuario"""
        qs = super().get_queryset(request)
        
        if hasattr(request, 'clinica_seleccionada') and request.clinica_seleccionada:
            qs = qs.filter(factura__clinica=request.clinica_seleccionada)
        
        return qs
