from django.contrib import admin
from .models import Clinica, Sucursal, Especialidad, Cubiculo


@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    """Administración de Clínicas"""
    list_display = ['nombre', 'pais', 'moneda', 'estado', 'fc']
    list_filter = ['estado', 'pais', 'fc']
    search_fields = ['nombre', 'email', 'telefono', 'ruc']
    readonly_fields = ['fc', 'fm', 'uc', 'um']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'eslogan', 'titulo_pestana', 'logo')
        }),
        ('Contacto', {
            'fields': ('direccion', 'telefono', 'email', 'sitio_web')
        }),
        ('Información Legal', {
            'fields': ('ruc', 'razon_social', 'representante_legal')
        }),
        ('Configuración Regional', {
            'fields': ('pais', 'moneda', 'zona_horaria')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    """Administración de Sucursales"""
    list_display = ['nombre', 'clinica', 'telefono', 'dias_atencion', 'estado', 'fc']
    list_filter = ['clinica', 'estado', 'fc']
    search_fields = ['nombre', 'direccion', 'telefono']
    readonly_fields = ['fc', 'fm', 'uc', 'um']
    
    fieldsets = (
        ('Información General', {
            'fields': ('clinica', 'nombre', 'direccion')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email')
        }),
        ('Horario Laboral', {
            'fields': (
                'horario_apertura', 'horario_cierre',
                'dias_atencion'
            )
        }),
        ('Horario Sábado', {
            'fields': (
                'sabado_horario_apertura',
                'sabado_horario_cierre'
            ),
            'classes': ('collapse',)
        }),
        ('Horario Domingo', {
            'fields': (
                'domingo_horario_apertura',
                'domingo_horario_cierre'
            ),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Administración de Especialidades"""
    list_display = ['nombre', 'duracion_default', 'color_calendario', 'estado', 'fc']
    list_filter = ['estado', 'fc']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fc', 'fm', 'uc', 'um', 'color_preview']
    
    fieldsets = (
        ('Información', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('duracion_default', 'color_calendario', 'color_preview')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def color_preview(self, obj):
        """Mostrar preview del color seleccionado"""
        if obj.color_calendario:
            return f'<div style="width: 50px; height: 50px; background-color: {obj.color_calendario}; border: 1px solid #ccc;"></div>'
        return '-'
    color_preview.allow_tags = True
    color_preview.short_description = 'Vista Previa'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)


@admin.register(Cubiculo)
class CubiculoAdmin(admin.ModelAdmin):
    """Administración de Cubículos"""
    list_display = ['nombre', 'sucursal', 'numero', 'capacidad', 'estado', 'fc']
    list_filter = ['sucursal__clinica', 'sucursal', 'estado', 'fc']
    search_fields = ['nombre', 'numero', 'sucursal__nombre']
    readonly_fields = ['fc', 'fm', 'uc', 'um']
    
    fieldsets = (
        ('Información', {
            'fields': ('sucursal', 'nombre', 'numero')
        }),
        ('Características', {
            'fields': ('capacidad', 'descripcion', 'equipamiento')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uc = request.user
        obj.um = request.user.id
        super().save_model(request, obj, form, change)
