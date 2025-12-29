from django.contrib import admin
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Administración de Pacientes"""
    list_display = ('get_full_name', 'cedula', 'genero', 'fecha_nacimiento', 'clinica', 'estado', 'fc')
    list_filter = ('estado', 'genero', 'clinica', 'fecha_nacimiento')
    search_fields = ('nombres', 'apellidos', 'cedula', 'telefono')
    readonly_fields = ('uc', 'fc', 'um', 'fm', 'get_edad')
    date_hierarchy = 'fecha_nacimiento'
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'cedula', 'genero', 'fecha_nacimiento', 'get_edad')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Información Médica', {
            'fields': ('alergias', 'medicamentos_actuales', 'condiciones_medicas')
        }),
        ('Contacto de Emergencia', {
            'fields': ('nombre_emergencia', 'parentesco_emergencia', 'telefono_emergencia')
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
    
    def get_full_name(self, obj):
        """Mostrar nombre completo del paciente"""
        return obj.get_nombre_completo()
    get_full_name.short_description = 'Nombre Completo'
    
    def get_edad(self, obj):
        """Mostrar edad del paciente"""
        return obj.get_edad()
    get_edad.short_description = 'Edad'
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que crea/modifica"""
        if not change:
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
