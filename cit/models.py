from django.db import models
from django.contrib.auth.models import User
from bases.models import ClaseModelo

# Create your models here.

class Clinica(ClaseModelo):
    """
    Modelo para representar una clínica odontológica.
    Una clínica puede tener múltiples sucursales.
    """
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Nombre de la Clínica'
    )
    direccion = models.TextField(
        verbose_name='Dirección',
        help_text='Dirección completa de la clínica principal'
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        help_text='Teléfono de contacto principal'
    )
    email = models.EmailField(
        verbose_name='Email',
        help_text='Email de contacto de la clínica'
    )
    
    class Meta:
        verbose_name = 'Clínica'
        verbose_name_plural = 'Clínicas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar que el teléfono no esté vacío
        if not self.telefono or len(self.telefono.strip()) < 7:
            raise ValidationError({
                'telefono': 'El teléfono debe tener al menos 7 caracteres'
            })
        
        # Normalizar nombre (capitalize)
        if self.nombre:
            self.nombre = self.nombre.strip().title()


class Sucursal(ClaseModelo):
    """
    Modelo para representar una sucursal de una clínica.
    Cada sucursal pertenece a una clínica y tiene horarios específicos.
    """
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name='sucursales',
        verbose_name='Clínica'
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre de la Sucursal'
    )
    direccion = models.TextField(
        verbose_name='Dirección',
        help_text='Dirección completa de la sucursal'
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        help_text='Teléfono de contacto de la sucursal'
    )
    horario_apertura = models.TimeField(
        verbose_name='Hora de Apertura',
        help_text='Hora de apertura (formato 24hrs)'
    )
    horario_cierre = models.TimeField(
        verbose_name='Hora de Cierre',
        help_text='Hora de cierre (formato 24hrs)'
    )
    dias_atencion = models.CharField(
        max_length=50,
        verbose_name='Días de Atención',
        help_text='Ej: Lunes a Viernes, Lunes a Sábado',
        default='Lunes a Viernes'
    )
    
    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['clinica', 'nombre']
        unique_together = [['clinica', 'nombre']]
    
    def __str__(self):
        return f"{self.clinica.nombre} - {self.nombre}"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar que horario de cierre sea después de apertura
        if self.horario_apertura and self.horario_cierre:
            if self.horario_cierre <= self.horario_apertura:
                raise ValidationError({
                    'horario_cierre': 'La hora de cierre debe ser posterior a la hora de apertura'
                })
        
        # Validar teléfono
        if not self.telefono or len(self.telefono.strip()) < 7:
            raise ValidationError({
                'telefono': 'El teléfono debe tener al menos 7 caracteres'
            })
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip().title()

