from django.contrib import admin
from .models import (
    Cita, ConfiguracionClinica, DisponibilidadDentista, ExcepcionDisponibilidad,
    ComisionDentista
)

# NOTA: Clinica, Sucursal, Especialidad, Cubiculo ahora se registran en clinicas/admin.py
# Esta app importa esos modelos solo para compatibilidad hacia atrás


# Dentista model moved to personal.models (SOOD-62 refactoring)
# Paciente model moved to pacientes.models (SOOD-62 refactoring)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """Administración de Citas"""
    list_display = ('get_info_cita', 'paciente', 'dentista', 'especialidad', 'fecha_hora', 'duracion', 'get_estado_badge_display', 'cubiculo')
    list_filter = ('estado', 'especialidad', 'dentista', 'cubiculo__sucursal', 'fecha_hora')
    search_fields = ('paciente__nombres', 'paciente__apellidos', 'paciente__cedula', 'dentista__usuario__first_name', 'dentista__usuario__last_name', 'observaciones')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    date_hierarchy = 'fecha_hora'
    list_per_page = 25
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': ('paciente',)
        }),
        ('Información de la Cita', {
            'fields': ('dentista', 'especialidad', 'cubiculo', 'fecha_hora', 'duracion')
        }),
        ('Estado y Observaciones', {
            'fields': ('estado', 'observaciones', 'motivo_cancelacion')
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_info_cita(self, obj):
        """Retorna información resumida de la cita"""
        return f"Cita #{obj.pk}"
    get_info_cita.short_description = 'ID'
    
    def get_estado_badge_display(self, obj):
        """Retorna el estado con formato HTML"""
        badge_info = obj.get_estado_badge()
        colores = {
            'warning': '#ffc107',
            'info': '#17a2b8',
            'primary': '#007bff',
            'success': '#28a745',
            'danger': '#dc3545',
            'secondary': '#6c757d',
        }
        color = colores.get(badge_info['color'], '#6c757d')
        return f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{badge_info["estado"]}</span>'
    get_estado_badge_display.short_description = 'Estado'
    get_estado_badge_display.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('paciente', 'dentista', 'dentista__usuario', 'especialidad', 'cubiculo', 'cubiculo__sucursal')


# ============================================================================
# ADMINS DE CONFIGURACIÓN Y DISPONIBILIDAD
# ============================================================================

@admin.register(ConfiguracionClinica)
class ConfiguracionClinicaAdmin(admin.ModelAdmin):
    """Administración de Configuración de Clínica"""
    list_display = ('sucursal', 'horario_inicio', 'horario_fin', 'duracion_slot', 'permitir_citas_mismo_dia', 'estado')
    list_filter = ('estado', 'permitir_citas_mismo_dia')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    
    fieldsets = (
        ('Sucursal', {
            'fields': ('sucursal',)
        }),
        ('Horarios Generales', {
            'fields': ('horario_inicio', 'horario_fin', 'duracion_slot')
        }),
        ('Días de Atención', {
            'fields': (
                'atiende_lunes', 'atiende_martes', 'atiende_miercoles',
                'atiende_jueves', 'atiende_viernes', 'atiende_sabado', 'atiende_domingo'
            )
        }),
        ('Horario Especial Sábado', {
            'fields': ('sabado_hora_inicio', 'sabado_hora_fin'),
            'classes': ('collapse',)
        }),
        ('Configuración de Citas', {
            'fields': ('permitir_citas_mismo_dia', 'horas_anticipacion_minima')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)


# ComisionDentistaInline, DisponibilidadDentistaInline moved to personal/admin.py (SOOD-62)
# DisponibilidadDentista, ExcepcionDisponibilidad, ComisionDentista admin moved to personal/admin.py (SOOD-62)

