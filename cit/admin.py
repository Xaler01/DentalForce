from django.contrib import admin
from .models import (
    Clinica, Sucursal, Especialidad, Cubiculo, Dentista, Paciente, Cita,
    ConfiguracionClinica, DisponibilidadDentista, ExcepcionDisponibilidad
)

# Register your models here.

class SucursalInline(admin.TabularInline):
    """Inline para mostrar sucursales dentro del admin de Clínica"""
    model = Sucursal
    extra = 1
    fields = ('nombre', 'direccion', 'telefono', 'horario_apertura', 'horario_cierre', 'estado')


class CubiculoInline(admin.TabularInline):
    """Inline para mostrar cubículos dentro del admin de Sucursal"""
    model = Cubiculo
    extra = 1
    fields = ('nombre', 'numero', 'capacidad', 'equipamiento', 'estado')



@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    """Administración de Clínicas"""
    list_display = ('nombre', 'telefono', 'email', 'estado', 'fc')
    list_filter = ('estado', 'fc')
    search_fields = ('nombre', 'email', 'telefono')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    inlines = [SucursalInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'direccion', 'telefono', 'email')
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
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    """Administración de Sucursales"""
    list_display = ('nombre', 'clinica', 'telefono', 'horario_apertura', 'horario_cierre', 'estado', 'fc')
    list_filter = ('clinica', 'estado', 'fc')
    search_fields = ('nombre', 'clinica__nombre', 'telefono')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    autocomplete_fields = ['clinica']
    inlines = [CubiculoInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('clinica', 'nombre', 'direccion', 'telefono')
        }),
        ('Horarios', {
            'fields': ('horario_apertura', 'horario_cierre', 'dias_atencion')
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
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Administración de Especialidades"""
    list_display = ('nombre', 'duracion_default', 'color_calendario', 'estado', 'fc')
    list_filter = ('estado', 'fc')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Configuración de Citas', {
            'fields': ('duracion_default', 'color_calendario')
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
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Cubiculo)
class CubiculoAdmin(admin.ModelAdmin):
    """Administración de Cubículos"""
    list_display = ('nombre', 'numero', 'sucursal', 'capacidad', 'estado', 'fc')
    list_filter = ('sucursal', 'estado', 'fc')
    search_fields = ('nombre', 'sucursal__nombre', 'sucursal__clinica__nombre')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    autocomplete_fields = ['sucursal']
    
    fieldsets = (
        ('Información General', {
            'fields': ('sucursal', 'nombre', 'numero')
        }),
        ('Configuración', {
            'fields': ('capacidad', 'equipamiento')
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
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    """Administración de Dentistas"""
    list_display = ('get_nombre_completo', 'cedula_profesional', 'sucursal_principal', 'get_especialidades_nombres', 'telefono_movil', 'estado', 'fc')
    list_filter = ('sucursal_principal', 'especialidades', 'estado', 'fc')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username', 'cedula_profesional', 'numero_licencia')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    autocomplete_fields = ['sucursal_principal']
    filter_horizontal = ['especialidades']
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario',)
        }),
        ('Datos Profesionales', {
            'fields': ('cedula_profesional', 'numero_licencia', 'especialidades', 'sucursal_principal')
        }),
        ('Información de Contacto', {
            'fields': ('telefono_movil',)
        }),
        ('Información Adicional', {
            'fields': ('fecha_contratacion', 'biografia', 'foto')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del dentista"""
        return f"Dr(a). {obj.usuario.get_full_name() or obj.usuario.username}"
    get_nombre_completo.short_description = 'Nombre'
    get_nombre_completo.admin_order_field = 'usuario__last_name'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Administración de Pacientes"""
    list_display = ('get_nombre_completo', 'cedula', 'get_edad', 'telefono', 'clinica', 'estado', 'fc')
    list_filter = ('clinica', 'genero', 'tipo_sangre', 'estado', 'fc')
    search_fields = ('nombres', 'apellidos', 'cedula', 'telefono', 'email')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    autocomplete_fields = ['clinica']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'cedula', 'fecha_nacimiento', 'genero')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Información Médica', {
            'fields': ('tipo_sangre', 'alergias', 'observaciones_medicas')
        }),
        ('Contacto de Emergencia', {
            'fields': ('contacto_emergencia_nombre', 'contacto_emergencia_telefono', 'contacto_emergencia_relacion')
        }),
        ('Clínica', {
            'fields': ('clinica',)
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del paciente"""
        return f"{obj.nombres} {obj.apellidos}"
    get_nombre_completo.short_description = 'Nombre Completo'
    get_nombre_completo.admin_order_field = 'apellidos'
    
    def get_edad(self, obj):
        """Retorna la edad del paciente"""
        return obj.get_edad()
    get_edad.short_description = 'Edad'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """Administración de Citas"""
    list_display = ('get_info_cita', 'paciente', 'dentista', 'especialidad', 'fecha_hora', 'duracion', 'get_estado_badge_display', 'cubiculo')
    list_filter = ('estado', 'especialidad', 'dentista', 'cubiculo__sucursal', 'fecha_hora')
    search_fields = ('paciente__nombres', 'paciente__apellidos', 'paciente__cedula', 'dentista__usuario__first_name', 'dentista__usuario__last_name', 'observaciones')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    autocomplete_fields = ['paciente', 'dentista', 'especialidad', 'cubiculo']
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


class DisponibilidadDentistaInline(admin.TabularInline):
    """Inline para mostrar disponibilidades dentro del admin de Dentista"""
    model = DisponibilidadDentista
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'activo')


@admin.register(DisponibilidadDentista)
class DisponibilidadDentistaAdmin(admin.ModelAdmin):
    """Administración de Disponibilidad de Dentistas"""
    list_display = ('dentista', 'dia_semana_display', 'hora_inicio', 'hora_fin', 'activo', 'estado')
    list_filter = ('dia_semana', 'activo', 'estado', 'dentista')
    search_fields = ('dentista__usuario__first_name', 'dentista__usuario__last_name')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    
    fieldsets = (
        ('Dentista', {
            'fields': ('dentista',)
        }),
        ('Disponibilidad', {
            'fields': ('dia_semana', 'hora_inicio', 'hora_fin', 'activo')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def dia_semana_display(self, obj):
        """Mostrar día de semana con formato"""
        return obj.get_dia_semana_display()
    dia_semana_display.short_description = 'Día de la Semana'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)


@admin.register(ExcepcionDisponibilidad)
class ExcepcionDisponibilidadAdmin(admin.ModelAdmin):
    """Administración de Excepciones de Disponibilidad"""
    list_display = ('dentista', 'tipo', 'fecha_inicio', 'fecha_fin', 'todo_el_dia', 'estado')
    list_filter = ('tipo', 'todo_el_dia', 'estado', 'fecha_inicio')
    search_fields = ('dentista__usuario__first_name', 'dentista__usuario__last_name', 'motivo')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Dentista', {
            'fields': ('dentista',)
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Tipo y Motivo', {
            'fields': ('tipo', 'motivo')
        }),
        ('Horario', {
            'fields': ('todo_el_dia', 'hora_inicio', 'hora_fin'),
            'description': 'Si no es todo el día, especificar el rango de horas de la excepción'
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
