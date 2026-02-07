from django.contrib import admin
from .models import (
    Dentista,
    ComisionDentista,
    DisponibilidadDentista,
    ExcepcionDisponibilidad,
    Personal,
    RegistroHorasPersonal,
    ExcepcionPersonal,
)


class ComisionDentistaInline(admin.TabularInline):
    """Inline para mostrar comisiones dentro del admin de Dentista"""
    model = ComisionDentista
    extra = 1
    fields = ('especialidad', 'tipo_comision', 'porcentaje', 'valor_fijo', 'activo')


class DisponibilidadDentistaInline(admin.TabularInline):
    """Inline para mostrar disponibilidades dentro del admin de Dentista"""
    model = DisponibilidadDentista
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'sucursal', 'activo')


@admin.register(Dentista)
class DentistaAdmin(admin.ModelAdmin):
    """Administración de Dentistas"""
    list_display = ('get_full_name', 'cedula_profesional', 'telefono_movil', 'sucursal_principal', 'estado', 'fc')
    list_filter = ('estado', 'sucursal_principal', 'fc')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'cedula_profesional', 'telefono_movil')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    inlines = [DisponibilidadDentistaInline, ComisionDentistaInline]
    filter_horizontal = ('especialidades', 'sucursales')
    
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('usuario',)
        }),
        ('Información Profesional', {
            'fields': ('cedula_profesional', 'numero_licencia', 'especialidades', 'biografia')
        }),
        ('Información de Contacto', {
            'fields': ('telefono_movil', 'foto')
        }),
        ('Información Laboral', {
            'fields': ('sucursal_principal', 'sucursales', 'fecha_contratacion')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Mostrar nombre completo del dentista"""
        return obj.usuario.get_full_name() or obj.usuario.username
    get_full_name.short_description = 'Nombre'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'tipo_personal', 'sucursal_principal', 'tipo_compensacion', 'estado')
    list_filter = ('tipo_personal', 'tipo_compensacion', 'estado')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    filter_horizontal = ('sucursales',)

    fieldsets = (
        ('Información de Usuario', {
            'fields': ('usuario', 'tipo_personal')
        }),
        ('Información Laboral', {
            'fields': ('sucursal_principal', 'sucursales', 'fecha_contratacion')
        }),
        ('Compensación', {
            'fields': ('tipo_compensacion', 'salario_mensual', 'tarifa_por_hora', 'tarifa_por_dia')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username
    get_full_name.short_description = 'Nombre'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(RegistroHorasPersonal)
class RegistroHorasPersonalAdmin(admin.ModelAdmin):
    list_display = ('personal', 'fecha', 'tipo_extra', 'horas', 'valor_total', 'estado')
    list_filter = ('estado', 'tipo_extra', 'fecha')
    search_fields = ('personal__usuario__first_name', 'personal__usuario__last_name')
    readonly_fields = ('uc', 'fc', 'um', 'fm')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExcepcionPersonal)
class ExcepcionPersonalAdmin(admin.ModelAdmin):
    list_display = ('personal', 'tipo', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('tipo', 'estado', 'fecha_inicio')
    search_fields = ('personal__usuario__first_name', 'personal__usuario__last_name')
    readonly_fields = ('uc', 'fc', 'um', 'fm')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(ComisionDentista)
class ComisionDentistaAdmin(admin.ModelAdmin):
    """Administración de Comisiones de Dentistas"""
    list_display = ('get_dentista_name', 'especialidad', 'tipo_comision', 'get_valor', 'activo', 'estado')
    list_filter = ('activo', 'estado', 'tipo_comision', 'especialidad')
    search_fields = ('dentista__usuario__first_name', 'dentista__usuario__last_name', 'especialidad__nombre')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    
    fieldsets = (
        ('Asignación', {
            'fields': ('dentista', 'especialidad')
        }),
        ('Configuración de Comisión', {
            'fields': ('tipo_comision', 'porcentaje', 'valor_fijo')
        }),
        ('Información Adicional', {
            'fields': ('observaciones', 'activo')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_dentista_name(self, obj):
        """Mostrar nombre del dentista"""
        return str(obj.dentista)
    get_dentista_name.short_description = 'Dentista'
    
    def get_valor(self, obj):
        """Mostrar valor de comisión"""
        if obj.tipo_comision == 'PORCENTAJE':
            return f"{obj.porcentaje}%" if obj.porcentaje else '-'
        else:
            return f"${obj.valor_fijo}" if obj.valor_fijo else '-'
    get_valor.short_description = 'Comisión'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(DisponibilidadDentista)
class DisponibilidadDentistaAdmin(admin.ModelAdmin):
    """Administración de Disponibilidades de Dentistas"""
    list_display = ('get_dentista_name', 'get_dia_display', 'hora_inicio', 'hora_fin', 'sucursal', 'activo', 'estado')
    list_filter = ('activo', 'estado', 'dia_semana', 'sucursal')
    search_fields = ('dentista__usuario__first_name', 'dentista__usuario__last_name')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    
    fieldsets = (
        ('Dentista', {
            'fields': ('dentista',)
        }),
        ('Horario', {
            'fields': ('dia_semana', 'hora_inicio', 'hora_fin')
        }),
        ('Sucursal', {
            'fields': ('sucursal',)
        }),
        ('Estado', {
            'fields': ('activo', 'estado')
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_dentista_name(self, obj):
        """Mostrar nombre del dentista"""
        return str(obj.dentista)
    get_dentista_name.short_description = 'Dentista'
    
    def get_dia_display(self, obj):
        """Mostrar nombre del día"""
        dias = dict(obj.DIAS_SEMANA)
        return dias.get(obj.dia_semana, str(obj.dia_semana))
    get_dia_display.short_description = 'Día'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExcepcionDisponibilidad)
class ExcepcionDisponibilidadAdmin(admin.ModelAdmin):
    """Administración de Excepciones de Disponibilidad"""
    list_display = ('get_dentista_name', 'tipo', 'fecha_inicio', 'fecha_fin', 'todo_el_dia', 'estado')
    list_filter = ('estado', 'tipo', 'todo_el_dia', 'fecha_inicio')
    search_fields = ('dentista__usuario__first_name', 'dentista__usuario__last_name', 'motivo')
    readonly_fields = ('uc', 'fc', 'um', 'fm')
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Dentista', {
            'fields': ('dentista',)
        }),
        ('Período', {
            'fields': ('fecha_inicio', 'fecha_fin', 'tipo')
        }),
        ('Detalles', {
            'fields': ('todo_el_dia', 'hora_inicio', 'hora_fin', 'motivo')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('uc', 'fc', 'um', 'fm'),
            'classes': ('collapse',)
        }),
    )
    
    def get_dentista_name(self, obj):
        """Mostrar nombre del dentista"""
        return str(obj.dentista)
    get_dentista_name.short_description = 'Dentista'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
