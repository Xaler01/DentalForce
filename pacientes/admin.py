from django.contrib import admin
from enfermedades.models import EnfermedadPaciente

from .models import Paciente


class EnfermedadPacienteInline(admin.TabularInline):
    """Inline para asignar enfermedades al paciente"""
    model = EnfermedadPaciente
    extra = 0
    autocomplete_fields = ['enfermedad']
    fields = (
        'enfermedad',
        'estado_actual',
        'fecha_diagnostico',
        'ultima_revision',
        'requiere_atencion_especial',
        'estado',
    )


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    """Administración de Pacientes"""
    list_display = (
        'get_full_name',
        'cedula',
        'genero',
        'fecha_nacimiento',
        'clinica',
        'es_vip',
        'categoria_vip',
        'estado',
        'fc'
    )
    list_filter = ('estado', 'genero', 'clinica', 'fecha_nacimiento', 'es_vip', 'categoria_vip')
    search_fields = ('nombres', 'apellidos', 'cedula', 'telefono')
    readonly_fields = ('uc', 'fc', 'um', 'fm', 'get_edad')
    inlines = [EnfermedadPacienteInline]
    date_hierarchy = 'fecha_nacimiento'
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'cedula', 'genero', 'fecha_nacimiento', 'get_edad')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Clasificación VIP', {
            'fields': ('es_vip', 'categoria_vip')
        }),
        ('Información Médica', {
            'fields': ('tipo_sangre', 'alergias', 'observaciones_medicas')
        }),
        ('Contacto de Emergencia', {
            'fields': (
                'contacto_emergencia_nombre',
                'contacto_emergencia_relacion',
                'contacto_emergencia_telefono'
            )
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
