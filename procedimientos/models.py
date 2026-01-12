"""
Modelos para el catálogo de procedimientos odontológicos.

Estructura:
- ProcedimientoOdontologico: Catálogo maestro de procedimientos
- ClinicaProcedimiento: Precios específicos por clínica
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ProcedimientoOdontologico(models.Model):
    """
    Catálogo maestro de procedimientos odontológicos.
    Basado en estructura híbrida inspirada en CDT de ADA.
    """
    
    CATEGORIA_CHOICES = [
        ('DIAGNOSTICO', 'Diagnóstico'),
        ('PREVENTIVA', 'Preventiva'),
        ('RESTAURATIVA', 'Restaurativa'),
        ('ENDODONCIA', 'Endodoncia'),
        ('PERIODONCIA', 'Periodoncia'),
        ('CIRUGIA', 'Cirugía Oral'),
        ('PROSTODONCIA', 'Prostodoncia'),
        ('IMPLANTES', 'Implantes'),
        ('ORTODONCIA', 'Ortodoncia'),
        ('URGENCIAS', 'Urgencias'),
        ('OTROS', 'Otros Servicios'),
    ]
    
    # Identificación
    codigo = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único del procedimiento (ej: RES-OBT001)"
    )
    codigo_cdt = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Código CDT equivalente (opcional, ej: D2140)"
    )
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre del procedimiento"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada del procedimiento"
    )
    
    # Clasificación
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        help_text="Categoría del procedimiento"
    )
    
    # Características del procedimiento
    duracion_estimada = models.IntegerField(
        validators=[MinValueValidator(5)],
        help_text="Duración estimada en minutos"
    )
    requiere_anestesia = models.BooleanField(
        default=False,
        help_text="¿Requiere anestesia local?"
    )
    afecta_odontograma = models.BooleanField(
        default=True,
        help_text="¿Afecta el estado de piezas dentales en el odontograma?"
    )
    
    # Estado
    estado = models.BooleanField(
        default=True,
        help_text="¿Procedimiento activo?"
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='procedimientos_creados'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='procedimientos_modificados',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Procedimiento Odontológico'
        verbose_name_plural = 'Procedimientos Odontológicos'
        ordering = ['categoria', 'codigo']
        indexes = [
            models.Index(fields=['categoria', 'estado']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def get_precio_para_clinica(self, clinica):
        """
        Obtiene el precio del procedimiento para una clínica específica.
        """
        try:
            cp = ClinicaProcedimiento.objects.get(
                clinica=clinica,
                procedimiento=self,
                activo=True
            )
            return cp.precio
        except ClinicaProcedimiento.DoesNotExist:
            return None


class ClinicaProcedimiento(models.Model):
    """
    Precios de procedimientos específicos por clínica.
    Permite que cada clínica maneje sus propios precios.
    """
    
    # Relaciones
    clinica = models.ForeignKey(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='precios_procedimientos'
    )
    procedimiento = models.ForeignKey(
        ProcedimientoOdontologico,
        on_delete=models.CASCADE,
        related_name='precios_por_clinica'
    )
    
    # Precio
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Precio del procedimiento en la moneda de la clínica"
    )
    moneda = models.CharField(
        max_length=3,
        default='USD',
        help_text="Código de moneda (USD, EUR, etc.)"
    )
    
    # Descuentos opcionales
    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Descuento en porcentaje (0-100)"
    )
    
    # Estado
    activo = models.BooleanField(
        default=True,
        help_text="¿Precio activo?"
    )
    
    # Notas
    notas = models.TextField(
        blank=True,
        help_text="Notas adicionales sobre el precio"
    )
    
    # Auditoría
    fc = models.DateTimeField(auto_now_add=True)
    fm = models.DateTimeField(auto_now=True)
    uc = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='precios_procedimientos_creados'
    )
    um = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='precios_procedimientos_modificados',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Precio de Procedimiento por Clínica'
        verbose_name_plural = 'Precios de Procedimientos por Clínica'
        unique_together = ('clinica', 'procedimiento')
        ordering = ['clinica', 'procedimiento']
        indexes = [
            models.Index(fields=['clinica', 'activo']),
            models.Index(fields=['procedimiento', 'activo']),
        ]
    
    def __str__(self):
        return f"{self.clinica.nombre} - {self.procedimiento.codigo}: ${self.precio}"
    
    def get_precio_con_descuento(self):
        """
        Calcula el precio final aplicando el descuento.
        """
        if self.descuento_porcentaje > 0:
            descuento = self.precio * (self.descuento_porcentaje / 100)
            return self.precio - descuento
        return self.precio
    
    def save(self, *args, **kwargs):
        """
        Override save para heredar moneda de la clínica.
        """
        if not self.moneda and self.clinica:
            self.moneda = self.clinica.moneda
        super().save(*args, **kwargs)
