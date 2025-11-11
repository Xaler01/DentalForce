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


class Especialidad(ClaseModelo):
    """
    Modelo para representar una especialidad odontológica.
    Define los tipos de servicios que puede ofrecer un dentista.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la Especialidad',
        help_text='Ej: Ortodoncia, Endodoncia, Periodoncia'
    )
    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción detallada de la especialidad',
        blank=True
    )
    duracion_default = models.PositiveIntegerField(
        verbose_name='Duración por Defecto (minutos)',
        help_text='Duración estimada de una cita de esta especialidad',
        default=30
    )
    color_calendario = models.CharField(
        max_length=7,
        verbose_name='Color para Calendario',
        help_text='Color en formato hexadecimal (Ej: #3498db)',
        default='#3498db'
    )
    
    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar duración mínima
        if self.duracion_default and self.duracion_default < 15:
            raise ValidationError({
                'duracion_default': 'La duración mínima debe ser de 15 minutos'
            })
        
        # Validar formato de color hexadecimal
        if self.color_calendario:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', self.color_calendario):
                raise ValidationError({
                    'color_calendario': 'El color debe estar en formato hexadecimal (Ej: #3498db)'
                })
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip().title()


class Cubiculo(ClaseModelo):
    """
    Modelo para representar un cubículo/consultorio dentro de una sucursal.
    Cada cubículo es donde se realizan las atenciones odontológicas.
    """
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='cubiculos',
        verbose_name='Sucursal'
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Cubículo',
        help_text='Ej: Consultorio 1, Sala de Cirugía'
    )
    numero = models.PositiveSmallIntegerField(
        verbose_name='Número',
        help_text='Número identificador del cubículo'
    )
    capacidad = models.PositiveSmallIntegerField(
        verbose_name='Capacidad',
        help_text='Número de personas que pueden estar simultáneamente',
        default=2
    )
    equipamiento = models.TextField(
        verbose_name='Equipamiento',
        help_text='Descripción del equipamiento disponible',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Cubículo'
        verbose_name_plural = 'Cubículos'
        ordering = ['sucursal', 'numero']
        unique_together = [['sucursal', 'numero']]
    
    def __str__(self):
        return f"{self.sucursal.nombre} - {self.nombre} (#{self.numero})"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar capacidad mínima (permite validar antes de llegar a la BD)
        if self.capacidad is not None and self.capacidad < 1:
            raise ValidationError({
                'capacidad': 'La capacidad mínima debe ser de 1 persona'
            })
        
        # Validar número positivo (permite validar antes de llegar a la BD)
        if self.numero is not None and self.numero < 1:
            raise ValidationError({
                'numero': 'El número del cubículo debe ser mayor a 0'
            })
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip().title()


class Dentista(ClaseModelo):
    """
    Modelo para representar un dentista/odontólogo.
    Cada dentista está vinculado a un usuario del sistema y puede tener múltiples especialidades.
    """
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dentista_profile',
        verbose_name='Usuario',
        help_text='Usuario del sistema asociado al dentista'
    )
    especialidades = models.ManyToManyField(
        Especialidad,
        related_name='dentistas',
        verbose_name='Especialidades',
        help_text='Especialidades que practica el dentista'
    )
    sucursal_principal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dentistas',
        verbose_name='Sucursal Principal',
        help_text='Sucursal donde trabaja principalmente'
    )
    cedula_profesional = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Cédula Profesional',
        help_text='Número de cédula profesional de odontología'
    )
    numero_licencia = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Número de Licencia',
        help_text='Número de licencia para ejercer'
    )
    telefono_movil = models.CharField(
        max_length=20,
        verbose_name='Teléfono Móvil',
        help_text='Número de teléfono móvil personal'
    )
    fecha_contratacion = models.DateField(
        verbose_name='Fecha de Contratación',
        help_text='Fecha en que inició labores'
    )
    biografia = models.TextField(
        verbose_name='Biografía',
        help_text='Descripción profesional, estudios, experiencia',
        blank=True
    )
    foto = models.ImageField(
        upload_to='dentistas/fotos/',
        verbose_name='Fotografía',
        help_text='Foto del dentista',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Dentista'
        verbose_name_plural = 'Dentistas'
        ordering = ['usuario__last_name', 'usuario__first_name']
    
    def __str__(self):
        return f"Dr(a). {self.usuario.get_full_name() or self.usuario.username}"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        import re
        
        # Validar cédula profesional (solo números y guiones)
        if self.cedula_profesional:
            if not re.match(r'^[0-9\-]+$', self.cedula_profesional):
                raise ValidationError({
                    'cedula_profesional': 'La cédula profesional solo puede contener números y guiones'
                })
        
        # Validar teléfono móvil
        if self.telefono_movil and len(self.telefono_movil.strip()) < 7:
            raise ValidationError({
                'telefono_movil': 'El teléfono móvil debe tener al menos 7 caracteres'
            })
        
        # Validar fecha de contratación (no puede ser futura)
        if self.fecha_contratacion:
            from datetime import date
            if self.fecha_contratacion > date.today():
                raise ValidationError({
                    'fecha_contratacion': 'La fecha de contratación no puede ser futura'
                })
    
    def get_especialidades_nombres(self):
        """Retorna una lista de nombres de especialidades"""
        return ", ".join([esp.nombre for esp in self.especialidades.all()])
    
    get_especialidades_nombres.short_description = 'Especialidades'

