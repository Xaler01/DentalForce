from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Odontograma,
    PiezaDental,
    HistoriaClinicaOdontologica,
    PlanTratamiento,
    ProcedimientoEnPlan,
    EvolucionConsulta,
    ProcedimientoEnEvolucion,
)


@admin.register(Odontograma)
class OdontogramaAdmin(admin.ModelAdmin):
    list_display = [
        'paciente',
        'tipo_denticion',
        'get_piezas_afectadas_badge',
        'fc',
    ]
    list_filter = [
        'tipo_denticion',
        'fc',
    ]
    search_fields = [
        'paciente__nombres',
        'paciente__apellidos',
    ]
    readonly_fields = [
        'fc',
        'fm',
        'uc',
        'um',
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': ('paciente', 'tipo_denticion'),
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',),
        }),
    )
    
    def get_piezas_afectadas_badge(self, obj):
        """Muestra el número de piezas afectadas con color"""
        count = obj.get_piezas_afectadas()
        if count == 0:
            color = 'green'
        elif count <= 3:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} piezas</span>',
            color,
            count
        )
    get_piezas_afectadas_badge.short_description = 'Piezas Afectadas'


@admin.register(PiezaDental)
class PiezaDentalAdmin(admin.ModelAdmin):
    list_display = [
        'numero',
        'nombre_anatomico',
        'odontograma_paciente',
        'estado_badge',
        'superficies_afectadas',
        'fecha_ultima_intervencion',
    ]
    list_filter = [
        'estado',
        'fecha_ultima_intervencion',
    ]
    search_fields = [
        'nombre_anatomico',
        'odontograma__paciente__nombres',
        'odontograma__paciente__apellidos',
    ]
    readonly_fields = [
        'fc',
        'fm',
        'uc',
        'um',
    ]
    fieldsets = (
        ('Información de la Pieza', {
            'fields': (
                'odontograma',
                'numero',
                'nombre_anatomico',
            ),
        }),
        ('Estado Clínico', {
            'fields': (
                'estado',
                'superficies_afectadas',
                'observaciones',
            ),
        }),
        ('Procedimientos', {
            'fields': (
                'procedimiento_realizado',
                'fecha_ultima_intervencion',
            ),
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',),
        }),
    )
    
    def odontograma_paciente(self, obj):
        paciente = obj.odontograma.paciente
        return f"{paciente.nombres} {paciente.apellidos}"
    odontograma_paciente.short_description = 'Paciente'
    
    def estado_badge(self, obj):
        """Muestra el estado con color"""
        color_map = {
            'SANA': 'green',
            'CARIES': 'red',
            'OBTURADA': 'blue',
            'CORONA': 'purple',
            'IMPLANTE': 'cyan',
            'AUSENTE': 'gray',
            'TRATAMIENTO': 'orange',
            'FRACTURA': 'darkred',
            'MOVILIDAD': 'orange',
        }
        color = color_map.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(HistoriaClinicaOdontologica)
class HistoriaClinicaOdontologicaAdmin(admin.ModelAdmin):
    list_display = [
        'paciente',
        'get_antecedentes_badge',
        'get_alergias_badge',
        'get_habitos_badge',
    ]
    list_filter = [
        'fuma',
        'consume_alcohol',
        'bruxismo',
        'presencia_caries',
        'fc',
    ]
    search_fields = [
        'paciente__nombres',
        'paciente__apellidos',
    ]
    readonly_fields = [
        'fc',
        'fm',
        'uc',
        'um',
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': ('paciente',),
        }),
        ('Antecedentes', {
            'fields': (
                'antecedentes_medicos',
                'antecedentes_odontologicos',
            ),
        }),
        ('Alergias y Medicamentos', {
            'fields': (
                'alergias',
                'medicamentos_actuales',
            ),
        }),
        ('Hábitos', {
            'fields': (
                'fuma',
                'consume_alcohol',
                'bruxismo',
            ),
        }),
        ('Higiene Oral', {
            'fields': (
                'frecuencia_cepillado',
                'usa_seda_dental',
            ),
        }),
        ('Examen Clínico', {
            'fields': (
                'estado_encias',
                'presencia_sarro',
                'presencia_caries',
                'observaciones_clinicas',
            ),
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',),
        }),
    )
    
    def get_antecedentes_badge(self, obj):
        if obj.antecedentes_medicos or obj.antecedentes_odontologicos:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px;">Sí</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">No</span>'
        )
    get_antecedentes_badge.short_description = 'Antecedentes'
    
    def get_alergias_badge(self, obj):
        if obj.alergias:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">Sí</span>'
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">No</span>'
        )
    get_alergias_badge.short_description = 'Alergias'
    
    def get_habitos_badge(self, obj):
        habitos = []
        if obj.fuma:
            habitos.append('Fuma')
        if obj.consume_alcohol:
            habitos.append('Alcohol')
        if obj.bruxismo:
            habitos.append('Bruxismo')
        
        if habitos:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                ', '.join(habitos)
            )
        return format_html(
            '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">Sin riesgo</span>'
        )
    get_habitos_badge.short_description = 'Hábitos'


class ProcedimientoEnPlanInline(admin.TabularInline):
    """Inline para procedimientos en un plan"""
    model = ProcedimientoEnPlan
    extra = 1
    fields = [
        'procedimiento',
        'orden',
        'precio',
        'realizado',
        'fecha_realizacion',
        'observaciones',
    ]
    autocomplete_fields = ['procedimiento']


@admin.register(PlanTratamiento)
class PlanTratamientoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'paciente',
        'get_estado_badge',
        'get_prioridad_badge',
        'get_progreso_bar',
        'get_presupuesto',
    ]
    list_filter = [
        'estado',
        'prioridad',
        'fc',
    ]
    search_fields = [
        'nombre',
        'paciente__nombres',
        'paciente__apellidos',
    ]
    readonly_fields = [
        'fc',
        'fm',
        'uc',
        'um',
    ]
    inlines = [ProcedimientoEnPlanInline]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'paciente',
                'nombre',
                'descripcion',
            ),
        }),
        ('Estado y Prioridad', {
            'fields': (
                'estado',
                'prioridad',
            ),
        }),
        ('Fechas', {
            'fields': (
                'fecha_inicio',
                'fecha_estimada_fin',
                'fecha_fin_real',
            ),
        }),
        ('Presupuesto', {
            'fields': (
                'presupuesto_estimado',
                'presupuesto_real',
            ),
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',),
        }),
    )
    
    def get_estado_badge(self, obj):
        color_map = {
            'PENDIENTE': 'gray',
            'ACTIVO': 'blue',
            'COMPLETADO': 'green',
            'CANCELADO': 'red',
        }
        color = color_map.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_estado_display()
        )
    get_estado_badge.short_description = 'Estado'
    
    def get_prioridad_badge(self, obj):
        color_map = {
            'URGENTE': 'red',
            'NECESARIO': 'orange',
            'ELECTIVO': 'green',
        }
        color = color_map.get(obj.prioridad, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_prioridad_display()
        )
    get_prioridad_badge.short_description = 'Prioridad'
    
    def get_progreso_bar(self, obj):
        progreso = obj.get_progreso()
        return format_html(
            '<div style="width: 100px; height: 20px; background-color: #f0f0f0; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background-color: #4CAF50;"></div>'
            '</div> {}%',
            progreso,
            progreso
        )
    get_progreso_bar.short_description = 'Progreso'
    
    def get_presupuesto(self, obj):
        return f"${obj.presupuesto_estimado:.2f}"
    get_presupuesto.short_description = 'Presupuesto'


class ProcedimientoEnEvolucionInline(admin.TabularInline):
    """Inline para procedimientos en una evolución"""
    model = ProcedimientoEnEvolucion
    extra = 1
    fields = [
        'procedimiento',
        'cantidad',
        'observaciones',
    ]
    autocomplete_fields = ['procedimiento']


@admin.register(EvolucionConsulta)
class EvolucionConsultaAdmin(admin.ModelAdmin):
    list_display = [
        'paciente',
        'fecha_consulta',
        'dentista',
        'get_motivo_badge',
        'get_num_procedimientos',
        'fecha_proximo_control',
    ]
    list_filter = [
        'fecha_consulta',
        'dentista',
        'fc',
    ]
    search_fields = [
        'paciente__nombres',
        'paciente__apellidos',
        'motivo_consulta',
    ]
    readonly_fields = [
        'fc',
        'fm',
        'uc',
        'um',
    ]
    inlines = [ProcedimientoEnEvolucionInline]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'paciente',
                'cita',
                'fecha_consulta',
                'dentista',
            ),
        }),
        ('Motivo de Consulta', {
            'fields': ('motivo_consulta',),
        }),
        ('Hallazgos Clínicos', {
            'fields': (
                'hallazgos_clinicos',
                'cambios_odontograma',
            ),
        }),
        ('Plan y Recomendaciones', {
            'fields': (
                'recomendaciones',
                'fecha_proximo_control',
            ),
        }),
        ('Auditoría', {
            'fields': ('fc', 'fm', 'uc', 'um'),
            'classes': ('collapse',),
        }),
    )
    
    def get_motivo_badge(self, obj):
        """Muestra un resumen del motivo de la consulta"""
        motivo = obj.motivo_consulta[:50]
        if len(obj.motivo_consulta) > 50:
            motivo += '...'
        return motivo
    get_motivo_badge.short_description = 'Motivo'
    
    def get_num_procedimientos(self, obj):
        """Muestra el número de procedimientos realizados"""
        count = obj.procedimientos.count()
        return format_html(
            '<span style="background-color: blue; color: white; padding: 3px 8px; border-radius: 3px;">{} procedimientos</span>',
            count
        )
    get_num_procedimientos.short_description = 'Procedimientos'
