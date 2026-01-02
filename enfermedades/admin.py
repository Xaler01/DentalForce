from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaEnfermedad, Enfermedad


@admin.register(CategoriaEnfermedad)
class CategoriaEnfermedadAdmin(admin.ModelAdmin):
    """
    Administración de Categorías de Enfermedades
    SOOD-71: Interface administrativa para gestión de categorías
    """
    list_display = (
        'nombre',
        'cantidad_enfermedades',
        'icono',
        'color',
        'orden',
        'estado',
        'fc',
        'uc'
    )
    list_filter = ('estado', 'fc')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')
    readonly_fields = ('fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', 'descripcion', 'estado')
        }),
        ('Presentación Visual', {
            'fields': ('icono', 'color', 'orden'),
            'description': 'Configuración de cómo se mostrará la categoría en el sistema'
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Enfermedad)
class EnfermedadAdmin(admin.ModelAdmin):
    """
    Administración de Enfermedades
    SOOD-72: Interface con filtros avanzados y vista detallada
    """
    list_display = (
        'nombre',
        'codigo_cie10',
        'categoria',
        'nivel_riesgo_badge',
        'requiere_interconsulta',
        'alertas_automaticas',
        'estado'
    )
    list_filter = (
        'nivel_riesgo',
        'categoria',
        'requiere_interconsulta',
        'genera_alerta_roja',
        'genera_alerta_amarilla',
        'estado'
    )
    search_fields = (
        'nombre',
        'nombre_cientifico',
        'codigo_cie10',
        'descripcion',
        'contraindicaciones'
    )
    ordering = ('categoria', 'nombre')
    readonly_fields = ('fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'categoria',
                'nombre',
                'nombre_cientifico',
                'codigo_cie10',
                'descripcion',
                'estado'
            )
        }),
        ('Clasificación de Riesgo', {
            'fields': ('nivel_riesgo', 'requiere_interconsulta'),
            'description': 'Nivel de riesgo determina precauciones durante tratamientos'
        }),
        ('Consideraciones Clínicas', {
            'fields': ('contraindicaciones', 'precauciones'),
            'classes': ('collapse',)
        }),
        ('Alertas Automáticas', {
            'fields': ('genera_alerta_roja', 'genera_alerta_amarilla'),
            'description': 'Enfermedades críticas generan alertas automáticas al paciente'
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )

    def nivel_riesgo_badge(self, obj):
        """Muestra el nivel de riesgo con badge colorido"""
        color = obj.get_color_riesgo()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_nivel_riesgo_display()
        )
    nivel_riesgo_badge.short_description = "Nivel de Riesgo"

    def alertas_automaticas(self, obj):
        """Muestra qué alertas genera automáticamente"""
        alertas = []
        if obj.genera_alerta_roja:
            alertas.append('<span style="color: #dc3545;">🔴 ROJA</span>')
        if obj.genera_alerta_amarilla:
            alertas.append('<span style="color: #ffc107;">🟡 AMARILLA</span>')
        if not alertas:
            return '-'
        return format_html(' / '.join(alertas))
    alertas_automaticas.short_description = "Alertas Auto"

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
