"""
Modelos para la evolución odontológica del paciente.

Estructura:
- Odontograma: Registro digital de piezas dentales y sus estados
- PiezaDental: Información de cada pieza dental (32 adulto, 20 pediátrico)
- HistoriaClinicaOdontologica: Historia clínica del paciente
- PlanTratamiento: Plan de procedimientos a realizar
- EvolucionConsulta: Notas por cada consulta/cita
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente
from procedimientos.models import ProcedimientoOdontologico


class Odontograma(models.Model):
    """
    Odontograma digital del paciente.
    Contiene el estado de todas las piezas dentales.
    """
    
    TIPO_DENTICION = [
        ('ADULTO', 'Dentición Adulta (32 piezas)'),
        ('PEDIÁTRICO', 'Dentición Pediátrica (20 piezas)'),
    ]
    
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name='odontograma'
    )
    tipo_denticion = models.CharField(
        max_length=20,
        choices=TIPO_DENTICION,
        default='ADULTO'
    )
    
    # Campos de auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='odontogramas_creados'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='odontogramas_modificados',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Odontograma'
        verbose_name_plural = 'Odontogramas'
    
    def __str__(self):
        return f"Odontograma de {self.paciente.nombres} ({self.get_tipo_denticion_display()})"
    
    def get_piezas_afectadas(self):
        """Obtiene el número de piezas con problemas."""
        return self.piezas.filter(
            estado__in=['CARIES', 'OBTURADA', 'AUSENTE', 'TRATAMIENTO']
        ).count()


class PiezaDental(models.Model):
    """
    Pieza dental individual en el odontograma.
    Cada pieza tiene un estado, superficies afectadas y observaciones.
    """
    
    ESTADO_CHOICES = [
        ('SANA', 'Sana'),
        ('CARIES', 'Caries'),
        ('OBTURADA', 'Obturada'),
        ('CORONA', 'Corona'),
        ('IMPLANTE', 'Implante'),
        ('AUSENTE', 'Ausente'),
        ('TRATAMIENTO', 'En Tratamiento'),
        ('FRACTURA', 'Fractura'),
        ('MOVILIDAD', 'Movilidad'),
    ]
    
    SUPERFICIE_CHOICES = [
        ('O', 'Oclusal'),
        ('M', 'Mesial'),
        ('D', 'Distal'),
        ('V', 'Vestibular'),
        ('P', 'Palatino/Lingual'),
    ]
    
    odontograma = models.ForeignKey(
        Odontograma,
        on_delete=models.CASCADE,
        related_name='piezas'
    )
    
    # Identificación de la pieza
    numero = models.IntegerField(
        help_text="Número de pieza dental (1-32 adulto, 1-20 pediátrico)"
    )
    nombre_anatomico = models.CharField(
        max_length=100,
        help_text="Nombre de la pieza (Incisivo Central Superior Derecho, etc.)"
    )
    
    # Estado actual
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='SANA'
    )
    
    # Superficies afectadas (puede tener múltiples)
    superficies_afectadas = models.CharField(
        max_length=20,
        blank=True,
        help_text="Superficies: O=Oclusal, M=Mesial, D=Distal, V=Vestibular, P=Palatino (ej: 'OM')"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones clínicas de la pieza"
    )
    
    # Procedimiento asociado
    procedimiento_realizado = models.ForeignKey(
        ProcedimientoOdontologico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='piezas_tratadas'
    )
    
    # Fechas
    fecha_ultima_intervencion = models.DateField(
        null=True,
        blank=True
    )
    
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='piezas_creadas'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='piezas_modificadas',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Pieza Dental'
        verbose_name_plural = 'Piezas Dentales'
        unique_together = ('odontograma', 'numero')
        ordering = ['numero']
    
    def __str__(self):
        return f"Pieza {self.numero}: {self.nombre_anatomico} ({self.get_estado_display()})"


class HistoriaClinicaOdontologica(models.Model):
    """
    Historia clínica odontológica del paciente.
    Contiene antecedentes, alergias, medicamentos, examen clínico.
    """
    
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name='historia_clinica_odontologica'
    )
    
    # Antecedentes
    antecedentes_medicos = models.TextField(
        blank=True,
        help_text="Enfermedades sistémicas, cirugías previas, etc."
    )
    antecedentes_odontologicos = models.TextField(
        blank=True,
        help_text="Procedimientos dentales previos, problemas dentales anteriores, etc."
    )
    
    # Alergias y medicamentos
    alergias = models.TextField(
        blank=True,
        help_text="Alergias a medicamentos, materiales dentales, etc."
    )
    medicamentos_actuales = models.TextField(
        blank=True,
        help_text="Medicamentos que está tomando actualmente"
    )
    
    # Hábitos
    fuma = models.BooleanField(
        default=False,
        help_text="¿Fuma?"
    )
    consume_alcohol = models.BooleanField(
        default=False,
        help_text="¿Consume alcohol?"
    )
    bruxismo = models.BooleanField(
        default=False,
        help_text="¿Padece bruxismo (rechina dientes)?"
    )
    
    # Higiene oral
    frecuencia_cepillado = models.CharField(
        max_length=50,
        blank=True,
        help_text="Frecuencia de cepillado diario (ej: 2-3 veces)"
    )
    usa_seda_dental = models.BooleanField(
        default=False,
        help_text="¿Usa seda dental?"
    )
    
    # Examen clínico
    estado_encias = models.TextField(
        blank=True,
        help_text="Observaciones sobre el estado de las encías"
    )
    presencia_sarro = models.BooleanField(
        default=False
    )
    presencia_caries = models.BooleanField(
        default=False
    )
    
    # Notas generales
    observaciones_clinicas = models.TextField(
        blank=True,
        help_text="Otras observaciones clínicas relevantes"
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='historias_clinicas_creadas'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='historias_clinicas_modificadas',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Historia Clínica Odontológica'
        verbose_name_plural = 'Historias Clínicas Odontológicas'
    
    def __str__(self):
        return f"Historia Clínica de {self.paciente.nombres}"

class PlanTratamiento(models.Model):
    """
    Plan de tratamiento del paciente.
    Lista de procedimientos a realizar con prioridades y presupuestos.
    """
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ACTIVO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('URGENTE', 'Urgente'),
        ('NECESARIO', 'Necesario'),
        ('ELECTIVO', 'Electivo'),
    ]
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='planes_tratamiento'
    )
    
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre del plan de tratamiento"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del plan"
    )
    
    # Estado y prioridad
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default='NECESARIO'
    )
    
    # Fechas
    fecha_inicio = models.DateField(
        null=True,
        blank=True
    )
    fecha_estimada_fin = models.DateField(
        null=True,
        blank=True
    )
    fecha_fin_real = models.DateField(
        null=True,
        blank=True
    )
    
    # Presupuesto
    presupuesto_estimado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Presupuesto total estimado"
    )
    presupuesto_real = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Presupuesto final real"
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='planes_creados'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='planes_modificados',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-prioridad', 'fecha_estimada_fin']
    
    def __str__(self):
        return f"Plan: {self.nombre} ({self.get_estado_display()})"
    
    def get_progreso(self):
        """Calcula el porcentaje de procedimientos completados."""
        total = self.procedimientos.count()
        if total == 0:
            return 0
        completados = self.procedimientos.filter(realizado=True).count()
        return int((completados / total) * 100)


class ProcedimientoEnPlan(models.Model):
    """
    Procedimiento dentro de un plan de tratamiento.
    """
    
    plan = models.ForeignKey(
        PlanTratamiento,
        on_delete=models.CASCADE,
        related_name='procedimientos'
    )
    
    procedimiento = models.ForeignKey(
        ProcedimientoOdontologico,
        on_delete=models.CASCADE,
        related_name='planes'
    )
    
    # Orden
    orden = models.IntegerField(
        default=0,
        help_text="Orden de ejecución del procedimiento"
    )
    
    # Precio
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio para este procedimiento en el plan"
    )
    
    # Estado
    realizado = models.BooleanField(
        default=False
    )
    fecha_realizacion = models.DateField(
        null=True,
        blank=True
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='procedimientos_plan_creados'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='procedimientos_plan_modificados',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Procedimiento en Plan'
        verbose_name_plural = 'Procedimientos en Plan'
        ordering = ['orden']
        unique_together = ('plan', 'procedimiento')
    
    def __str__(self):
        return f"{self.procedimiento.codigo} en {self.plan.nombre}"


class EvolucionConsulta(models.Model):
    """
    Nota de evolución por cada consulta/cita del paciente.
    Registro de procedimientos realizados, observaciones, evolución.
    """
    
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='evoluciones'
    )
    
    # Referencia a la cita (opcional)
    cita = models.OneToOneField(
        'cit.Cita',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evolucion'
    )
    
    # Fecha
    fecha_consulta = models.DateField()
    
    # Dentista que realizó la consulta
    dentista = models.ForeignKey(
        'personal.Dentista',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evoluciones'
    )
    
    # Motivo de consulta
    motivo_consulta = models.TextField(
        help_text="Queja principal del paciente"
    )
    
    # Procedimientos realizados
    procedimientos_realizados = models.ManyToManyField(
        ProcedimientoOdontologico,
        through='ProcedimientoEnEvolucion',
        related_name='evoluciones'
    )
    
    # Hallazgos
    hallazgos_clinicos = models.TextField(
        blank=True,
        help_text="Hallazgos clínicos encontrados durante la consulta"
    )
    
    # Plan de tratamiento
    recomendaciones = models.TextField(
        blank=True,
        help_text="Recomendaciones para el paciente"
    )
    
    # Cambios en el odontograma
    cambios_odontograma = models.TextField(
        blank=True,
        help_text="Cambios realizados en el odontograma"
    )
    
    # Próxima cita
    fecha_proximo_control = models.DateField(
        null=True,
        blank=True
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evoluciones_creadas'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evoluciones_modificadas',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Evolución de Consulta'
        verbose_name_plural = 'Evoluciones de Consulta'
        ordering = ['-fecha_consulta']
        indexes = [
            models.Index(fields=['paciente', '-fecha_consulta']),
        ]
    
    def __str__(self):
        return f"Evolución {self.paciente.nombres} - {self.fecha_consulta}"

class ProcedimientoEnEvolucion(models.Model):
    """
    Procedimiento realizado en una evolución de consulta.
    """
    
    evolucion = models.ForeignKey(
        EvolucionConsulta,
        on_delete=models.CASCADE,
        related_name='procedimientos'
    )
    
    procedimiento = models.ForeignKey(
        ProcedimientoOdontologico,
        on_delete=models.CASCADE
    )
    
    # Cantidad realizada
    cantidad = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    # Observaciones específicas del procedimiento
    observaciones = models.TextField(
        blank=True
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    
    class Meta:
        verbose_name = 'Procedimiento en Evolución'
        verbose_name_plural = 'Procedimientos en Evolución'
        unique_together = ('evolucion', 'procedimiento')
    
    def __str__(self):
        return f"{self.procedimiento.codigo} en consulta {self.evolucion.fecha_consulta}"
