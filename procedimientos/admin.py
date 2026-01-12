"""
Admin interface para el catálogo de procedimientos odontológicos.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ProcedimientoOdontologico, ClinicaProcedimiento


@admin.register(ProcedimientoOdontologico)
class ProcedimientoOdontologicoAdmin(admin.ModelAdmin):
    """
    Admin para el catálogo maestro de procedimientos odontológicos.
    """
    list_display = [
        'codigo',
        'nombre',
        'categoria_badge',
        'duracion_estimada',
        'requiere_anestesia_icon',
        'estado_badge',
        'fc',
    ]
    list_filter = ['categoria', 'estado', 'requiere_anestesia', 'afecta_odontograma']
    search_fields = ['codigo', 'nombre', 'descripcion', 'codigo_cdt']
    readonly_fields = ['fc', 'fm', 'uc', 'um']
    autocomplete_fields = []  # No tiene relaciones para autocomplete
    
    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'codigo_cdt', 'nombre', 'descripcion')
        }),
        ('Clasificación', {
            'fields': ('categoria',)
        }),
        ('Características', {
            'fields': ('duracion_estimada', 'requiere_anestesia', 'afecta_odontograma')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def categoria_badge(self, obj):
        """Muestra la categoría con color."""
        colors = {
            'DIAGNOSTICO': '#17a2b8',
            'PREVENTIVA': '#28a745',
            'RESTAURATIVA': '#007bff',
            'ENDODONCIA': '#dc3545',
            'PERIODONCIA': '#fd7e14',
            'CIRUGIA': '#6f42c1',
            'PROSTODONCIA': '#20c997',
            'IMPLANTES': '#6c757d',
            'ORTODONCIA': '#e83e8c',
            'URGENCIAS': '#ffc107',
            'OTROS': '#6c757d',
        }
        color = colors.get(obj.categoria, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'
    
    def requiere_anestesia_icon(self, obj):
        """Muestra ícono si requiere anestesia."""
        if obj.requiere_anestesia:
            return format_html('<span style="color: #dc3545;">💉</span>')
        return format_html('<span style="color: #6c757d;">-</span>')
    requiere_anestesia_icon.short_description = 'Anestesia'
    
    def estado_badge(self, obj):
        """Muestra el estado con badge."""
        if obj.estado:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">Inactivo</span>'
        )
    estado_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que crea o modifica."""
        if not change:
            obj.uc = request.user
        else:
            obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClinicaProcedimiento)
class ClinicaProcedimientoAdmin(admin.ModelAdmin):
    """
    Admin para precios de procedimientos por clínica.
    """
    list_display = [
        'clinica',
        'procedimiento_codigo',
        'procedimiento_nombre',
        'precio_formateado',
        'descuento_badge',
        'precio_final_formateado',
        'activo_badge',
    ]
    list_filter = ['clinica', 'activo', 'procedimiento__categoria']
    search_fields = [
        'clinica__nombre',
        'procedimiento__codigo',
        'procedimiento__nombre'
    ]
    readonly_fields = ['fc', 'fm', 'uc', 'um', 'precio_con_descuento_display']
    autocomplete_fields = ['procedimiento']
    
    fieldsets = (
        ('Relaciones', {
            'fields': ('clinica', 'procedimiento')
        }),
        ('Precio', {
            'fields': ('precio', 'moneda', 'descuento_porcentaje', 'precio_con_descuento_display')
        }),
        ('Estado y Notas', {
            'fields': ('activo', 'notas')
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def procedimiento_codigo(self, obj):
        """Muestra el código del procedimiento."""
        return obj.procedimiento.codigo
    procedimiento_codigo.short_description = 'Código'
    procedimiento_codigo.admin_order_field = 'procedimiento__codigo'
    
    def procedimiento_nombre(self, obj):
        """Muestra el nombre del procedimiento."""
        return obj.procedimiento.nombre
    procedimiento_nombre.short_description = 'Procedimiento'
    procedimiento_nombre.admin_order_field = 'procedimiento__nombre'
    
    def precio_formateado(self, obj):
        """Muestra el precio formateado."""
        return f"${obj.precio:,.2f} {obj.moneda}"
    precio_formateado.short_description = 'Precio Base'
    
    def descuento_badge(self, obj):
        """Muestra el descuento como badge."""
        if obj.descuento_porcentaje > 0:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 11px;">-{}%</span>',
                obj.descuento_porcentaje
            )
        return '-'
    descuento_badge.short_description = 'Descuento'
    
    def precio_final_formateado(self, obj):
        """Muestra el precio final con descuento."""
        precio_final = obj.get_precio_con_descuento()
        if obj.descuento_porcentaje > 0:
            return format_html(
                '<strong style="color: #28a745;">${:,.2f} {}</strong>',
                precio_final,
                obj.moneda
            )
        return f"${precio_final:,.2f} {obj.moneda}"
    precio_final_formateado.short_description = 'Precio Final'
    
    def precio_con_descuento_display(self, obj):
        """Campo readonly para mostrar el precio con descuento."""
        if obj.pk:
            precio_final = obj.get_precio_con_descuento()
            return f"${precio_final:,.2f} {obj.moneda}"
        return '-'
    precio_con_descuento_display.short_description = 'Precio con Descuento'
    
    def activo_badge(self, obj):
        """Muestra el estado activo como badge."""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">Inactivo</span>'
        )
    activo_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que crea o modifica."""
        if not change:
            obj.uc = request.user
        else:
            obj.um = request.user
        super().save_model(request, obj, form, change)
