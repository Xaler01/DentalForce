from django.contrib import admin
from .models import UsuarioClinica, RolUsuario


@admin.register(UsuarioClinica)
class UsuarioClinicaAdmin(admin.ModelAdmin):
    """Admin para gestionar usuarios por clínica"""
    
    list_display = ('usuario_email', 'nombre_completo', 'clinica', 'rol', 'activo', 'fecha_creacion')
    list_filter = ('clinica', 'rol', 'activo', 'fecha_creacion')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name')
    readonly_fields = ('usuario', 'fecha_creacion', 'fecha_modificacion')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Asignación de Clínica', {
            'fields': ('clinica', 'rol')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_inactivo', 'marcar_activo']
    
    def usuario_email(self, obj):
        """Mostrar email del usuario en lista"""
        return obj.usuario.email
    usuario_email.short_description = 'Email'
    
    def nombre_completo(self, obj):
        """Mostrar nombre completo en lista"""
        return obj.usuario.get_full_name() or obj.usuario.email
    nombre_completo.short_description = 'Nombre Completo'
    
    def marcar_inactivo(self, request, queryset):
        """Acción: marcar usuarios como inactivos (soft delete)"""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} usuario(s) marcado(s) como inactivo(s).')
    marcar_inactivo.short_description = 'Marcar como inactivo'
    
    def marcar_activo(self, request, queryset):
        """Acción: marcar usuarios como activos"""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} usuario(s) marcado(s) como activo(s).')
    marcar_activo.short_description = 'Marcar como activo'

