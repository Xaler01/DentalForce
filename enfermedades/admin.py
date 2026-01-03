from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente, AlertaPaciente


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


@admin.register(Enfermedad)
class EnfermedadAdmin(admin.ModelAdmin):
    """
    Administración de Enfermedades
    SOOD-72: Interface con filtros avanzados y vista detallada
    """
    list_display = (
        'nombre',
        'codigo_cie10',
        'categoria',
        'nivel_riesgo_badge',
        'requiere_interconsulta',
        'alertas_automaticas',
        'estado'
    )
    list_filter = (
        'nivel_riesgo',
        'categoria',
        'requiere_interconsulta',
        'genera_alerta_roja',
        'genera_alerta_amarilla',
        'estado'
    )
    search_fields = (
        'nombre',
        'nombre_cientifico',
        'codigo_cie10',
        'descripcion',
        'contraindicaciones'
    )
    ordering = ('categoria', 'nombre')
    readonly_fields = ('fc', 'fm', 'uc', 'um')
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'categoria',
                'nombre',
                'nombre_cientifico',
                'codigo_cie10',
                'descripcion',
                'estado'
            )
        }),
        ('Clasificación de Riesgo', {
            'fields': ('nivel_riesgo', 'requiere_interconsulta'),
            'description': 'Nivel de riesgo determina precauciones durante tratamientos'
        }),
        ('Consideraciones Clínicas', {
            'fields': ('contraindicaciones', 'precauciones'),
            'classes': ('collapse',)
        }),
        ('Alertas Automáticas', {
            'fields': ('genera_alerta_roja', 'genera_alerta_amarilla'),
            'description': 'Enfermedades críticas generan alertas automáticas al paciente'
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )

    def nivel_riesgo_badge(self, obj):
        """Muestra el nivel de riesgo con badge colorido"""
        color = obj.get_color_riesgo()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_nivel_riesgo_display()
        )
    nivel_riesgo_badge.short_description = "Nivel de Riesgo"

    def alertas_automaticas(self, obj):
        """Muestra qué alertas genera automáticamente"""
        alertas = []
        if obj.genera_alerta_roja:
            alertas.append('<span style="color: #dc3545;">🔴 ROJA</span>')
        if obj.genera_alerta_amarilla:
            alertas.append('<span style="color: #ffc107;">🟡 AMARILLA</span>')
        if not alertas:
            return '-'
        return format_html(' / '.join(alertas))
    alertas_automaticas.short_description = "Alertas Auto"

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(EnfermedadPaciente)
class EnfermedadPacienteAdmin(admin.ModelAdmin):
    """
    Administración de relación Paciente-Enfermedad
    SOOD-73: Gestión de enfermedades asignadas a pacientes
    """
    list_display = (
        'paciente',
        'enfermedad',
        'estado_actual',
        'fecha_diagnostico',
        'dias_revision',
        'requiere_atencion',
        'estado'
    )
    list_filter = (
        'estado_actual',
        'requiere_atencion_especial',
        'enfermedad__nivel_riesgo',
        'enfermedad__categoria',
        'estado',
        'fecha_diagnostico'
    )
    search_fields = (
        'paciente__nombres',
        'paciente__apellidos',
        'paciente__cedula',
        'enfermedad__nombre',
        'medicacion_actual',
        'observaciones'
    )
    ordering = ('-fecha_diagnostico', 'paciente')
    readonly_fields = ('fc', 'fm', 'uc', 'um', 'dias_desde_diagnostico_display')
    autocomplete_fields = ['paciente', 'enfermedad']
    
    fieldsets = (
        ('Relación Principal', {
            'fields': ('paciente', 'enfermedad', 'estado')
        }),
        ('Información Clínica', {
            'fields': (
                'fecha_diagnostico',
                'estado_actual',
                'medicacion_actual',
                'observaciones'
            )
        }),
        ('Control y Seguimiento', {
            'fields': (
                'ultima_revision',
                'requiere_atencion_especial',
                'dias_desde_diagnostico_display'
            )
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',)
        }),
    )

    def dias_revision(self, obj):
        """Muestra días desde última revisión con color"""
        dias = obj.dias_desde_revision()
        if dias is None:
            return '-'
        
        if dias > 180:  # 6 meses
            color = '#dc3545'  # Rojo
            icono = '⚠️'
        elif dias > 90:  # 3 meses
            color = '#ffc107'  # Amarillo
            icono = '⏰'
        else:
            color = '#28a745'  # Verde
            icono = '✓'
        
        return format_html(
            '<span style="color: {};">{} {} días</span>',
            color, icono, dias
        )
    dias_revision.short_description = "Última Revisión"

    def requiere_atencion(self, obj):
        """Muestra si requiere atención especial"""
        if obj.requiere_atencion_especial:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠️ SÍ</span>')
        return '-'
    requiere_atencion.short_description = "Atención Especial"

    def dias_desde_diagnostico_display(self, obj):
        """Muestra días desde diagnóstico (readonly)"""
        dias = obj.dias_desde_diagnostico()
        if dias is None:
            return "No especificado"
        
        años = dias // 365
        meses = (dias % 365) // 30
        
        if años > 0:
            return f"{años} año(s) y {meses} mes(es)"
        elif meses > 0:
            return f"{meses} mes(es)"
        else:
            return f"{dias} día(s)"
    dias_desde_diagnostico_display.short_description = "Tiempo desde diagnóstico"

    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)


@admin.register(AlertaPaciente)
class AlertaPacienteAdmin(admin.ModelAdmin):
    """
    Administración de Alertas de Pacientes
    SOOD-77: Gestión y seguimiento de alertas automáticas
    """
    list_display = (
        'paciente_link',
        'nivel_badge',
        'tipo_display',
        'titulo',
        'es_activa',
        'requiere_accion',
        'vista_badge',
        'fc'
    )
    list_filter = (
        'nivel',
        'tipo',
        'es_activa',
        'requiere_accion',
        ('vista_por', admin.RelatedOnlyFieldListFilter),
        'fc'
    )
    search_fields = (
        'paciente__nombres',
        'paciente__apellidos',
        'paciente__cedula',
        'titulo',
        'descripcion'
    )
    ordering = ('-fc', '-nivel')
    readonly_fields = (
        'fc',
        'fm',
        'uc',
        'um',
        'fecha_vista_display',
        'dias_desde_creacion'
    )
    
    fieldsets = (
        ('Información de la Alerta', {
            'fields': (
                'paciente',
                'nivel',
                'tipo',
                'titulo',
                'descripcion'
            )
        }),
        ('Enfermedades Relacionadas', {
            'fields': ('enfermedades_relacionadas',),
            'classes': ('collapse',)
        }),
        ('Estado y Seguimiento', {
            'fields': (
                'es_activa',
                'requiere_accion',
                'fecha_vencimiento',
                'vista_por',
                'fecha_vista_display',
                'notas_seguimiento'
            )
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um', 'dias_desde_creacion'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('enfermedades_relacionadas',)
    
    def paciente_link(self, obj):
        """Link al paciente"""
        if obj.paciente:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:pacientes_paciente_change', args=[obj.paciente.id])
            return format_html('<a href="{}">{}</a>', url, obj.paciente)
        return '-'
    paciente_link.short_description = 'Paciente'
    
    def nivel_badge(self, obj):
        """Badge coloreado según nivel"""
        colores = {
            'VERDE': '#28a745',
            'AMARILLO': '#ffc107',
            'ROJO': '#dc3545',
        }
        color = colores.get(obj.nivel, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_nivel_display()
        )
    nivel_badge.short_description = 'Nivel'
    
    def tipo_display(self, obj):
        """Tipo de alerta con icono"""
        iconos = {
            'ENFERMEDAD_CRITICA': '🔴',
            'ENFERMEDAD_ALTA': '🟠',
            'VIP_MANUAL': '⭐',
            'VIP_FACTURACION': '💰',
            'MULTIPLES_CONDICIONES': '📋',
            'REQUIERE_INTERCONSULTA': '👨‍⚕️',
            'SISTEMA': '⚙️',
        }
        icono = iconos.get(obj.tipo, '📌')
        return f"{icono} {obj.get_tipo_display()}"
    tipo_display.short_description = 'Tipo'
    
    def vista_badge(self, obj):
        """Badge indicando si fue vista"""
        if obj.vista_por and obj.fecha_vista:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.vista_por.get_full_name() or obj.vista_por.username
            )
        if obj.requiere_accion:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Pendiente</span>')
        return '-'
    vista_badge.short_description = 'Revisión'
    
    def fecha_vista_display(self, obj):
        """Muestra fecha de vista formateada"""
        if obj.fecha_vista:
            return obj.fecha_vista.strftime('%d/%m/%Y %H:%M')
        return 'No revisada'
    fecha_vista_display.short_description = 'Fecha de Revisión'
    
    def dias_desde_creacion(self, obj):
        """Días desde que se creó la alerta"""
        from django.utils import timezone
        delta = timezone.now() - obj.fc
        dias = delta.days
        if dias == 0:
            return 'Hoy'
        elif dias == 1:
            return '1 día'
        else:
            return f'{dias} días'
    dias_desde_creacion.short_description = 'Antigüedad'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo asignando usuario de creación/modificación"""
        if not change:  # Nuevo registro
            obj.uc = request.user
        obj.um = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['marcar_como_vistas', 'desactivar_alertas']
    
    def marcar_como_vistas(self, request, queryset):
        """Acción para marcar alertas como vistas"""
        count = 0
        for alerta in queryset:
            if not alerta.vista_por:
                alerta.marcar_como_vista(request.user)
                count += 1
        self.message_user(request, f'{count} alerta(s) marcada(s) como vista(s).')
    marcar_como_vistas.short_description = "Marcar como vistas"
    
    def desactivar_alertas(self, request, queryset):
        """Acción para desactivar alertas"""
        count = queryset.filter(es_activa=True).update(
            es_activa=False,
            um=request.user.id
        )
        self.message_user(request, f'{count} alerta(s) desactivada(s).')
    desactivar_alertas.short_description = "Desactivar alertas seleccionadas"

