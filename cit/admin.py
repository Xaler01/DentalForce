from django.contrib import admin
from .models import Clinica, Sucursal

# Register your models here.

class SucursalInline(admin.TabularInline):
    """Inline para mostrar sucursales dentro del admin de Clínica"""
    model = Sucursal
    extra = 1
    fields = ('nombre', 'direccion', 'telefono', 'horario_apertura', 'horario_cierre', 'estado')


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

