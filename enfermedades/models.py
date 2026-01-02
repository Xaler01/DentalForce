from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from bases.models import ClaseModelo


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
        'pacientes.Paciente',
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
