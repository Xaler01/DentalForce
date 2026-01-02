from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente


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


@admin.register(EnfermedadPaciente)
class EnfermedadPacienteAdmin(admin.ModelAdmin):
    """
    Administración de relación Paciente-Enfermedad
    SOOD-73: Gestión de enfermedades asignadas a pacientes
    """
    list_display = (
        'paciente',
        'enfermedad',
        'estado_actual',
        'fecha_diagnostico',
        'dias_revision',
        'requiere_atencion',
        'estado'
    )
    list_filter = (
        'estado_actual',
        'requiere_atencion_especial',
        'enfermedad__nivel_riesgo',
        'enfermedad__categoria',
        'estado',
        'fecha_diagnostico'
    )
    search_fields = (
        'paciente__nombres',
        'paciente__apellidos',
        'paciente__cedula',
        'enfermedad__nombre',
        'medicacion_actual',
        'observaciones'
    )
    ordering = ('-fecha_diagnostico', 'paciente')
    readonly_fields = ('fc', 'fm', 'uc', 'um', 'dias_desde_diagnostico_display')
    autocomplete_fields = ['paciente', 'enfermedad']
    
    fieldsets = (
        ('Relación Principal', {
            'fields': ('paciente', 'enfermedad', 'estado')
        }),
        ('Información Clínica', {
            'fields': (
                'fecha_diagnostico',
                'estado_actual',
                'medicacion_actual',
                'observaciones'
            )
        }),
        ('Control y Seguimiento', {
            'fields': (
                'ultima_revision',
                'requiere_atencion_especial',
                'dias_desde_diagnostico_display'
            )
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )

    def dias_revision(self, obj):
        """Muestra días desde última revisión con color"""
        dias = obj.dias_desde_revision()
        if dias is None:
            return '-'
        
        if dias > 180:  # 6 meses
            color = '#dc3545'  # Rojo
            icono = '⚠️'
        elif dias > 90:  # 3 meses
            color = '#ffc107'  # Amarillo
            icono = '⏰'
        else:
            color = '#28a745'  # Verde
            icono = '✓'
        
        return format_html(
            '<span style="color: {};">{} {} días</span>',
            color, icono, dias
        )
    dias_revision.short_description = "Última Revisión"

    def requiere_atencion(self, obj):
        """Muestra si requiere atención especial"""
        if obj.requiere_atencion_especial:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠️ SÍ</span>')
        return '-'
    requiere_atencion.short_description = "Atención Especial"

    def dias_desde_diagnostico_display(self, obj):
        """Muestra días desde diagnóstico (readonly)"""
        dias = obj.dias_desde_diagnostico()
        if dias is None:
            return "No especificado"
        
        años = dias // 365
        meses = (dias % 365) // 30
        
        if años > 0:
            return f"{años} año(s) y {meses} mes(es)"
        elif meses > 0:
            return f"{meses} mes(es)"
        else:
            return f"{dias} día(s)"
    dias_desde_diagnostico_display.short_description = "Tiempo desde diagnóstico"

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
