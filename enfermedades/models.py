from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from bases.models import ClaseModelo
from pacientes.models import Paciente
from clinicas.models import Clinica


class CategoriaEnfermedad(ClaseModelo):
    """
    Categorías para clasificar enfermedades (Ej: Cardiovascular, Endocrinológica, etc.)
    SOOD-71: Modelo base para organización jerárquica de enfermedades
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre de la categoría (Ej: Cardiovascular, Respiratoria)"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada de la categoría"
    )
    icono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Clase de icono FontAwesome (Ej: fa-heart, fa-lungs)"
    )
    color = models.CharField(
        max_length=20,
        default='#6c757d',
        help_text="Color hexadecimal para identificación visual"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de presentación (menor = primero)"
    )

    class Meta:
        verbose_name = "Categoría de Enfermedad"
        verbose_name_plural = "Categorías de Enfermedades"
        ordering = ['orden', 'nombre']
        db_table = 'enf_categoria'

    def __str__(self):
        return self.nombre

    def cantidad_enfermedades(self):
        """Retorna la cantidad de enfermedades activas en esta categoría"""
        return self.enfermedades.filter(estado=True).count()
    cantidad_enfermedades.short_description = "Enfermedades"


class Enfermedad(ClaseModelo):
    """
    Catálogo de enfermedades preexistentes con niveles de riesgo
    SOOD-72: Modelo principal con 51 enfermedades clasificadas
    """
    NIVEL_RIESGO_CHOICES = [
        ('BAJO', 'Bajo - Requiere monitoreo estándar'),
        ('MEDIO', 'Medio - Precauciones adicionales'),
        ('ALTO', 'Alto - Consulta médica previa'),
        ('CRITICO', 'Crítico - Atención especializada urgente'),
    ]

    categoria = models.ForeignKey(
        CategoriaEnfermedad,
        on_delete=models.PROTECT,
        related_name='enfermedades',
        help_text="Categoría a la que pertenece esta enfermedad"
    )
    nombre = models.CharField(
        max_length=200,
        unique=True,
        help_text="Nombre común de la enfermedad"
    )
    nombre_cientifico = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre médico/científico (opcional)"
    )
    codigo_cie10 = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        unique=True,
        help_text="Código CIE-10 (Clasificación Internacional de Enfermedades)"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción médica de la enfermedad"
    )
    nivel_riesgo = models.CharField(
        max_length=10,
        choices=NIVEL_RIESGO_CHOICES,
        default='MEDIO',
        help_text="Nivel de riesgo odontológico"
    )
    
    # Consideraciones clínicas
    contraindicaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Tratamientos o medicamentos contraindicados"
    )
    precauciones = models.TextField(
        blank=True,
        null=True,
        help_text="Precauciones especiales durante procedimientos"
    )
    requiere_interconsulta = models.BooleanField(
        default=False,
        help_text="¿Requiere consulta médica previa al tratamiento?"
    )
    
    # Alertas automáticas
    genera_alerta_roja = models.BooleanField(
        default=False,
        help_text="Si está activo, genera automáticamente alerta ROJA"
    )
    genera_alerta_amarilla = models.BooleanField(
        default=False,
        help_text="Si está activo, genera automáticamente alerta AMARILLA"
    )

    class Meta:
        verbose_name = "Enfermedad"
        verbose_name_plural = "Enfermedades"
        ordering = ['categoria', 'nombre']
        db_table = 'enf_enfermedad'
        indexes = [
            models.Index(fields=['nivel_riesgo']),
            models.Index(fields=['codigo_cie10']),
        ]

    def __str__(self):
        if self.codigo_cie10:
            return f"{self.nombre} ({self.codigo_cie10})"
        return self.nombre

    def get_color_riesgo(self):
        """Retorna el color asociado al nivel de riesgo"""
        colores = {
            'BAJO': '#28a745',      # Verde
            'MEDIO': '#ffc107',     # Amarillo
            'ALTO': '#fd7e14',      # Naranja
            'CRITICO': '#dc3545',   # Rojo
        }
        return colores.get(self.nivel_riesgo, '#6c757d')
    
    def get_icono_riesgo(self):
        """Retorna el icono FontAwesome según el nivel de riesgo"""
        iconos = {
            'BAJO': 'fa-check-circle',
            'MEDIO': 'fa-exclamation-triangle',
            'ALTO': 'fa-exclamation-circle',
            'CRITICO': 'fa-times-circle',
        }
        return iconos.get(self.nivel_riesgo, 'fa-info-circle')


class EnfermedadPaciente(ClaseModelo):
    """
    Relación M2M entre Paciente y Enfermedad (Through model)
    SOOD-73: Permite registrar enfermedades con contexto adicional
    """
    ESTADO_ENFERMEDAD_CHOICES = [
        ('ACTIVA', 'Activa - Bajo tratamiento actual'),
        ('CONTROLADA', 'Controlada - Con medicación'),
        ('REMISION', 'En Remisión - Sin síntomas'),
        ('CURADA', 'Curada - Ya no requiere tratamiento'),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='enfermedades_paciente',
        help_text="Paciente que padece la enfermedad"
    )
    enfermedad = models.ForeignKey(
        Enfermedad,
        on_delete=models.PROTECT,
        related_name='pacientes_afectados',
        help_text="Enfermedad diagnosticada"
    )
    
    # Contexto clínico
    fecha_diagnostico = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de diagnóstico (si se conoce)"
    )
    estado_actual = models.CharField(
        max_length=15,
        choices=ESTADO_ENFERMEDAD_CHOICES,
        default='ACTIVA',
        help_text="Estado actual de la enfermedad"
    )
    medicacion_actual = models.TextField(
        blank=True,
        null=True,
        help_text="Medicamentos actuales relacionados con esta enfermedad"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Notas clínicas adicionales del dentista"
    )
    
    # Control
    ultima_revision = models.DateField(
        blank=True,
        null=True,
        help_text="Última vez que se revisó/actualizó esta información"
    )
    requiere_atencion_especial = models.BooleanField(
        default=False,
        help_text="Marcar si requiere consideraciones especiales urgentes"
    )

    class Meta:
        verbose_name = "Enfermedad del Paciente"
        verbose_name_plural = "Enfermedades de Pacientes"
        unique_together = [('paciente', 'enfermedad')]
        ordering = ['-fecha_diagnostico', 'enfermedad__nombre']
        db_table = 'enf_enfermedad_paciente'
        indexes = [
            models.Index(fields=['paciente', 'estado_actual']),
            models.Index(fields=['enfermedad', 'estado_actual']),
        ]

    def __str__(self):
        return f"{self.paciente} - {self.enfermedad} ({self.estado_actual})"

    def save(self, *args, **kwargs):
        """
        Guarda y actualiza la última revisión
        """
        if not self.ultima_revision:
            self.ultima_revision = timezone.now().date()
        super().save(*args, **kwargs)

    def dias_desde_diagnostico(self):
        """Calcula días transcurridos desde el diagnóstico"""
        if not self.fecha_diagnostico:
            return None
        delta = timezone.now().date() - self.fecha_diagnostico
        return delta.days

    def dias_desde_revision(self):
        """Calcula días desde la última revisión"""
        if not self.ultima_revision:
            return None
        delta = timezone.now().date() - self.ultima_revision
        return delta.days

    def requiere_actualizacion(self, dias=180):
        """Verifica si la información requiere actualización (default 6 meses)"""
        dias_revision = self.dias_desde_revision()
        if dias_revision is None:
            return True
        return dias_revision > dias


class AlertaPaciente(ClaseModelo):
    """
    Sistema de Alertas de Pacientes
    SOOD-77: Registro histórico de alertas generadas automáticamente
    """
    NIVEL_ALERTA_CHOICES = [
        ('VERDE', 'Verde - Sin riesgos identificados'),
        ('AMARILLO', 'Amarillo - Precauciones necesarias'),
        ('ROJO', 'Rojo - Atención prioritaria/VIP'),
    ]
    
    TIPO_ALERTA_CHOICES = [
        ('ENFERMEDAD_CRITICA', 'Enfermedad Crítica'),
        ('ENFERMEDAD_ALTA', 'Enfermedad de Alto Riesgo'),
        ('VIP_MANUAL', 'Cliente VIP (Manual)'),
        ('VIP_FACTURACION', 'Cliente VIP (por Facturación)'),
        ('MULTIPLES_CONDICIONES', 'Múltiples Condiciones Médicas'),
        ('REQUIERE_INTERCONSULTA', 'Requiere Interconsulta Médica'),
        ('SISTEMA', 'Alerta del Sistema'),
    ]
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='alertas',
        help_text="Paciente al que pertenece esta alerta"
    )
    
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_ALERTA_CHOICES,
        help_text="Nivel de severidad de la alerta"
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_ALERTA_CHOICES,
        help_text="Tipo/origen de la alerta"
    )
    
    titulo = models.CharField(
        max_length=200,
        help_text="Título descriptivo de la alerta"
    )
    
    descripcion = models.TextField(
        help_text="Descripción detallada de la alerta"
    )
    
    # Metadatos adicionales
    enfermedades_relacionadas = models.ManyToManyField(
        Enfermedad,
        blank=True,
        related_name='alertas_generadas',
        help_text="Enfermedades que provocaron esta alerta"
    )
    
    requiere_accion = models.BooleanField(
        default=True,
        help_text="Si requiere acción inmediata del personal"
    )
    
    es_activa = models.BooleanField(
        default=True,
        help_text="Si la alerta sigue vigente"
    )
    
    fecha_vencimiento = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha en que la alerta deja de ser relevante (opcional)"
    )
    
    # Seguimiento
    vista_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas_vistas',
        help_text="Usuario que revisó la alerta"
    )
    
    fecha_vista = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha en que se revisó la alerta"
    )
    
    notas_seguimiento = models.TextField(
        blank=True,
        null=True,
        help_text="Notas del personal sobre el seguimiento"
    )

    class Meta:
        verbose_name = "Alerta de Paciente"
        verbose_name_plural = "Alertas de Pacientes"
        ordering = ['-fc', '-nivel']  # Más recientes primero, rojas primero
        db_table = 'enf_alerta_paciente'
        indexes = [
            models.Index(fields=['paciente', 'nivel', 'es_activa']),
            models.Index(fields=['nivel', 'es_activa', '-fc']),
            models.Index(fields=['tipo', 'es_activa']),
        ]

    def __str__(self):
        return f"{self.paciente} - {self.get_nivel_display()} - {self.titulo}"

    def marcar_como_vista(self, usuario):
        """Marca la alerta como vista por un usuario"""
        self.vista_por = usuario
        self.fecha_vista = timezone.now()
        self.save(update_fields=['vista_por', 'fecha_vista', 'fm', 'um'])

    def desactivar(self, razon=None):
        """Desactiva la alerta"""
        self.es_activa = False
        if razon:
            self.notas_seguimiento = (self.notas_seguimiento or "") + f"\nDesactivada: {razon}"
        self.save(update_fields=['es_activa', 'notas_seguimiento', 'fm', 'um'])

    def esta_vencida(self):
        """Verifica si la alerta ha vencido"""
        if not self.fecha_vencimiento:
            return False
        return timezone.now() > self.fecha_vencimiento

    def get_color_badge(self):
        """Retorna el color CSS para el badge según el nivel"""
        colores = {
            'VERDE': 'success',
            'AMARILLO': 'warning',
            'ROJO': 'danger',
        }
        return colores.get(self.nivel, 'secondary')

    def get_icono(self):
        """Retorna el icono FontAwesome según el nivel"""
        iconos = {
            'VERDE': 'fa-check-circle',
            'AMARILLO': 'fa-exclamation-triangle',
            'ROJO': 'fa-exclamation-circle',
        }
        return iconos.get(self.nivel, 'fa-info-circle')


class ClinicaEnfermedad(ClaseModelo):
    """
    Configuración por clínica del catálogo global de Enfermedades.

    Permite habilitar/deshabilitar u ocultar una enfermedad específica
    para una clínica determinada, así como definir un nombre personalizado.

    - No modifica el estado global de la enfermedad
    - No afecta a otras clínicas
    - Si no existe un registro para (clinica, enfermedad), se considera habilitada por defecto
    """
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name='config_enfermedades',
        help_text='Clínica a la que aplica esta configuración'
    )
    enfermedad = models.ForeignKey(
        Enfermedad,
        on_delete=models.PROTECT,
        related_name='configuraciones',
        help_text='Enfermedad del catálogo global'
    )
    habilitada = models.BooleanField(
        default=True,
        help_text='Si está deshabilitada, no se muestra/usa en esta clínica'
    )
    ocultar = models.BooleanField(
        default=False,
        help_text='Si está activa pero oculta, no aparece en listados'
    )
    nombre_personalizado = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Nombre alternativo usado por esta clínica (opcional)'
    )
    notas = models.TextField(
        blank=True,
        null=True,
        help_text='Notas internas sobre esta configuración'
    )

    class Meta:
        verbose_name = 'Configuración de Enfermedad por Clínica'
        verbose_name_plural = 'Configuraciones de Enfermedades por Clínica'
        unique_together = [['clinica', 'enfermedad']]
        ordering = ['clinica__nombre', 'enfermedad__nombre']
        db_table = 'enf_clinica_enfermedad'
        indexes = [
            models.Index(fields=['clinica', 'habilitada', 'ocultar']),
            models.Index(fields=['enfermedad', 'habilitada', 'ocultar'])
        ]

    def __str__(self):
        base = self.nombre_personalizado or self.enfermedad.nombre
        estado = 'habilitada' if self.habilitada else 'deshabilitada'
        if self.ocultar:
            estado += ', oculta'
        return f"{self.clinica.nombre} → {base} ({estado})"

    @property
    def nombre_para_clinica(self):
        return self.nombre_personalizado or self.enfermedad.nombre


