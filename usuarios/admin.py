from django.contrib import admin
from .models import UsuarioClinica, RolUsuario, PermisoPersonalizado, RolUsuarioDentalForce


@admin.register(PermisoPersonalizado)
class PermisoPersonalizadoAdmin(admin.ModelAdmin):
    """Admin para gestionar permisos granulares"""
    
    list_display = ('codigo', 'nombre', 'categoria', 'clinica', 'activo', 'fecha_creacion')
    list_filter = ('categoria', 'clinica', 'activo', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    ordering = ('categoria', 'codigo')
    
    fieldsets = (
        ('Información del Permiso', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Alcance', {
            'fields': ('clinica',),
            'description': 'Vacío = Permiso global del sistema. Seleccionar = Permiso personalizado para clínica'
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filtrar según permisos del usuario"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Admin de clínica: solo ver permisos de su clínica y globales
            try:
                clinica = request.user.clinica_asignacion.clinica
                from django.db.models import Q
                qs = qs.filter(Q(clinica=None) | Q(clinica=clinica))
            except:
                qs = qs.none()
        return qs


@admin.register(RolUsuarioDentalForce)
class RolUsuarioDentalForceAdmin(admin.ModelAdmin):
    """Admin para gestionar roles con permisos"""
    
    list_display = ('nombre', 'clinica', 'permisos_count', 'activo', 'fecha_creacion')
    list_filter = ('clinica', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    ordering = ('nombre',)
    filter_horizontal = ('permisos',)
    
    fieldsets = (
        ('Información del Rol', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Alcance', {
            'fields': ('clinica',),
            'description': 'Vacío = Rol global del sistema. Seleccionar = Rol personalizado para clínica'
        }),
        ('Permisos', {
            'fields': ('permisos',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def permisos_count(self, obj):
        """Mostrar cantidad de permisos"""
        return obj.permisos.count()
    permisos_count.short_description = 'Permisos'
    
    def get_queryset(self, request):
        """Filtrar según permisos del usuario"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Admin de clínica: solo ver roles de su clínica y globales
            try:
                clinica = request.user.clinica_asignacion.clinica
                from django.db.models import Q
                qs = qs.filter(Q(clinica=None) | Q(clinica=clinica))
            except:
                qs = qs.none()
        return qs


@admin.register(UsuarioClinica)
class UsuarioClinicaAdmin(admin.ModelAdmin):
    """Admin para gestionar usuarios por clínica"""
    
    list_display = ('usuario_email', 'nombre_completo', 'clinica', 'rol', 'activo', 'fecha_creacion')
    list_filter = ('clinica', 'rol', 'activo', 'fecha_creacion')
    search_fields = ('usuario__email', 'usuario__first_name', 'usuario__last_name')
    readonly_fields = ('usuario', 'fecha_creacion', 'fecha_modificacion')
    ordering = ('-fecha_creacion',)
    filter_horizontal = ('roles_personalizados', 'permisos_adicionales')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Asignación de Clínica', {
            'fields': ('clinica', 'rol')
        }),
        ('Roles (Nueva Arquitectura)', {
            'fields': ('roles_personalizados',),
            'description': 'Múltiples roles para mayor flexibilidad. Usuario puede tener varios roles simultáneamente.',
            'classes': ('collapse',)
        }),
        ('Permisos Adicionales', {
            'fields': ('permisos_adicionales',),
            'description': 'Permisos granulares adicionales más allá de los incluidos en roles',
            'classes': ('collapse',)
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

