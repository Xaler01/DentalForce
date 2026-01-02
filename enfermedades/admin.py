from django.contrib import admin
from .models import CategoriaEnfermedad


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
