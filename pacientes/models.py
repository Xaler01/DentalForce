"""
Pacientes app models: Paciente
Moved from cit.models during SOOD-62 refactoring.
"""
from django.db import models
from bases.models import ClaseModelo
from clinicas.models import Clinica


class Paciente(ClaseModelo):
    """
    Modelo para representar un paciente de la clínica.
    Almacena información personal, médica y de contacto.
    """
    # Información Personal
    nombres = models.CharField(
        max_length=100,
        verbose_name='Nombres',
        help_text='Nombres del paciente'
    )
    apellidos = models.CharField(
        max_length=100,
        verbose_name='Apellidos',
        help_text='Apellidos del paciente'
    )
    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Cédula/DNI',
        help_text='Número de identificación único'
    )
    fecha_nacimiento = models.DateField(
        verbose_name='Fecha de Nacimiento',
        help_text='Fecha de nacimiento del paciente'
    )
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    genero = models.CharField(
        max_length=1,
        choices=GENERO_CHOICES,
        verbose_name='Género'
    )
    
    # Información de Contacto
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        help_text='Número de teléfono principal'
    )
    email = models.EmailField(
        verbose_name='Email',
        blank=True,
        help_text='Correo electrónico (opcional)'
    )
    direccion = models.TextField(
        verbose_name='Dirección',
        help_text='Dirección de domicilio'
    )
    
    # Información Médica
    TIPO_SANGRE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    tipo_sangre = models.CharField(
        max_length=3,
        choices=TIPO_SANGRE_CHOICES,
        verbose_name='Tipo de Sangre',
        blank=True
    )
    alergias = models.TextField(
        verbose_name='Alergias',
        help_text='Alergias conocidas del paciente',
        blank=True
    )
    observaciones_medicas = models.TextField(
        verbose_name='Observaciones Médicas',
        help_text='Condiciones médicas, medicamentos, etc.',
        blank=True
    )
    
    # Contacto de Emergencia
    contacto_emergencia_nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre del Contacto de Emergencia',
        help_text='Nombre completo del contacto',
        blank=True,
        default=''
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono de Emergencia',
        help_text='Teléfono del contacto de emergencia',
        blank=True,
        default=''
    )
    contacto_emergencia_relacion = models.CharField(
        max_length=50,
        verbose_name='Relación',
        help_text='Parentesco o relación (Ej: Madre, Esposo)',
        blank=True
    )
    
    # Foto del Paciente
    foto = models.ImageField(
        upload_to='pacientes/fotos/',
        verbose_name='Fotografía',
        help_text='Foto del paciente (opcional)',
        blank=True,
        null=True
    )
    
    # Relación con Clínica
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.PROTECT,
        related_name='pacientes',
        verbose_name='Clínica',
        help_text='Clínica donde está registrado el paciente',
        null=True,
        blank=True
    )

    def __init__(self, *args, **kwargs):
        # Compatibility for fixtures/tests that use 'sexo' instead of 'genero'
        if 'sexo' in kwargs and 'genero' not in kwargs:
            kwargs['genero'] = kwargs.pop('sexo')
        super().__init__(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['apellidos', 'nombres']
    
    def __str__(self):
        return f"{self.apellidos}, {self.nombres} - {self.cedula}"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        from datetime import date
        
        # Validar que la fecha de nacimiento no sea futura
        if self.fecha_nacimiento:
            if self.fecha_nacimiento > date.today():
                raise ValidationError({
                    'fecha_nacimiento': 'La fecha de nacimiento no puede ser futura'
                })
            
            # Validar que el paciente no sea menor de 1 año ni mayor de 150 años
            edad = (date.today() - self.fecha_nacimiento).days // 365
            if edad < 0 or edad > 150:
                raise ValidationError({
                    'fecha_nacimiento': 'Fecha de nacimiento inválida (edad debe estar entre 0 y 150 años)'
                })
        
        # Validar teléfono
        if self.telefono and len(self.telefono.strip()) < 7:
            raise ValidationError({
                'telefono': 'El teléfono debe tener al menos 7 caracteres'
            })
        
        # Validar teléfono de emergencia
        if self.contacto_emergencia_telefono and len(self.contacto_emergencia_telefono.strip()) < 7:
            raise ValidationError({
                'contacto_emergencia_telefono': 'El teléfono de emergencia debe tener al menos 7 caracteres'
            })
        
        # Validar cédula (solo números y guiones)
        if self.cedula:
            import re
            if not re.match(r'^[0-9\-]+$', self.cedula):
                raise ValidationError({
                    'cedula': 'La cédula solo puede contener números y guiones'
                })
        
        # Normalizar nombres y apellidos
        if self.nombres:
            self.nombres = self.nombres.strip().title()
        if self.apellidos:
            self.apellidos = self.apellidos.strip().title()
    
    def get_edad(self):
        """Retorna la edad del paciente en años"""
        from datetime import date
        if self.fecha_nacimiento:
            hoy = date.today()
            return (hoy - self.fecha_nacimiento).days // 365
        return None
    
    get_edad.short_description = 'Edad'
    
    def get_nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        return f"{self.nombres} {self.apellidos}"
    
    get_nombre_completo.short_description = 'Nombre Completo'

