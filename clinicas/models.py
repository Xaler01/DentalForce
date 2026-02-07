from django.db import models
from django.core.exceptions import ValidationError
from bases.models import ClaseModelo


class Clinica(ClaseModelo):
    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre de la Clínica')
    direccion = models.TextField(verbose_name='Dirección', help_text='Dirección completa de la clínica principal')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono', help_text='Teléfono de contacto principal')
    email = models.EmailField(verbose_name='Email', help_text='Email de contacto de la clínica')

    eslogan = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name='Eslogan',
        help_text='Frase corta y memorable (máx. 80 caracteres). Ej: "Gestión clínica"'
    )
    titulo_pestana = models.CharField(
        max_length=180,
        blank=True,
        null=True,
        verbose_name='Título de Pestaña Personalizado',
        help_text='Texto a mostrar en la pestaña del navegador (opcional). Si no llenan, usará: Nombre | Eslogan'
    )

    ruc = models.CharField(max_length=20, blank=True, null=True, verbose_name='RUC/NIT/CUIT')
    razon_social = models.CharField(max_length=200, blank=True, null=True, verbose_name='Razón Social')
    representante_legal = models.CharField(max_length=150, blank=True, null=True, verbose_name='Representante Legal')

    PAISES_CHOICES = [
        ('EC', 'Ecuador'),
        ('PE', 'Perú'),
        ('CO', 'Colombia'),
        ('MX', 'México'),
        ('CL', 'Chile'),
        ('AR', 'Argentina'),
    ]

    MONEDA_CHOICES = [
        ('USD', 'Dólar Estadounidense'),
        ('PEN', 'Sol Peruano'),
        ('COP', 'Peso Colombiano'),
        ('MXN', 'Peso Mexicano'),
        ('CLP', 'Peso Chileno'),
        ('ARS', 'Peso Argentino'),
    ]

    pais = models.CharField(max_length=2, choices=PAISES_CHOICES, default='EC', verbose_name='País')
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default='USD', verbose_name='Moneda')
    zona_horaria = models.CharField(max_length=50, default='America/Guayaquil', verbose_name='Zona Horaria')

    logo = models.ImageField(upload_to='clinicas/logos/', blank=True, null=True, verbose_name='Logo')
    sitio_web = models.URLField(blank=True, null=True, verbose_name='Sitio Web')

    class Meta:
        verbose_name = 'Clínica'
        verbose_name_plural = 'Clínicas'
        ordering = ['nombre']
        db_table = 'clinicas_clinica'

    def __str__(self):
        return self.nombre

    def clean(self):
        # Validar que el teléfono no esté vacío
        if not self.telefono or len(self.telefono.strip()) < 7:
            raise ValidationError({'telefono': 'El teléfono debe tener al menos 7 caracteres'})

        if self.nombre:
            self.nombre = self.nombre.strip().title()

    def get_nombre_completo(self):
        return self.razon_social if self.razon_social else self.nombre


class Sucursal(ClaseModelo):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='sucursales', verbose_name='Clínica')
    nombre = models.CharField(max_length=150, verbose_name='Nombre de la Sucursal')
    direccion = models.TextField(verbose_name='Dirección', help_text='Dirección completa de la sucursal')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono', help_text='Teléfono de contacto de la sucursal')
    email = models.EmailField(blank=True, null=True, verbose_name='Email', help_text='Email de contacto de la sucursal')
    horario_apertura = models.TimeField(verbose_name='Hora de Apertura', blank=True, null=True)
    horario_cierre = models.TimeField(verbose_name='Hora de Cierre', blank=True, null=True)
    dias_atencion = models.CharField(max_length=50, default='Lunes a Viernes', verbose_name='Días de Atención')

    sabado_horario_apertura = models.TimeField(blank=True, null=True, verbose_name='Sábado - Hora de Apertura')
    sabado_horario_cierre = models.TimeField(blank=True, null=True, verbose_name='Sábado - Hora de Cierre')

    domingo_horario_apertura = models.TimeField(blank=True, null=True, verbose_name='Domingo - Hora de Apertura')
    domingo_horario_cierre = models.TimeField(blank=True, null=True, verbose_name='Domingo - Hora de Cierre')

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        ordering = ['clinica', 'nombre']
        unique_together = [['clinica', 'nombre']]
        db_table = 'clinicas_sucursal'

    def __str__(self):
        return f"{self.clinica.nombre} - {self.nombre}"

    def get_horario_dia(self, dia):
        if dia == 'S' and self.sabado_horario_apertura:
            return {'apertura': self.sabado_horario_apertura, 'cierre': self.sabado_horario_cierre}
        elif dia == 'D' and self.domingo_horario_apertura:
            return {'apertura': self.domingo_horario_apertura, 'cierre': self.domingo_horario_cierre}
        else:
            return {'apertura': self.horario_apertura, 'cierre': self.horario_cierre}

    def clean(self):
        if self.horario_apertura and self.horario_cierre:
            if self.horario_cierre <= self.horario_apertura:
                raise ValidationError({'horario_cierre': 'La hora de cierre debe ser posterior a la hora de apertura'})

        if self.sabado_horario_apertura or self.sabado_horario_cierre:
            if not (self.sabado_horario_apertura and self.sabado_horario_cierre):
                raise ValidationError({'sabado_horario_apertura': 'Debe especificar tanto apertura como cierre para sábado'})
            if self.sabado_horario_cierre <= self.sabado_horario_apertura:
                raise ValidationError({'sabado_horario_cierre': 'La hora de cierre de sábado debe ser posterior a la hora de apertura'})

        if self.domingo_horario_apertura or self.domingo_horario_cierre:
            if not (self.domingo_horario_apertura and self.domingo_horario_cierre):
                raise ValidationError({'domingo_horario_apertura': 'Debe especificar tanto apertura como cierre para domingo'})
            if self.domingo_horario_cierre <= self.domingo_horario_apertura:
                raise ValidationError({'domingo_horario_cierre': 'La hora de cierre de domingo debe ser posterior a la hora de apertura'})

        if not self.telefono or len(self.telefono.strip()) < 7:
            raise ValidationError({'telefono': 'El teléfono debe tener al menos 7 caracteres'})

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
        import re
        
        # Validar duración mínima
        if self.duracion_default and self.duracion_default < 15:
            raise ValidationError({
                'duracion_default': 'La duración mínima debe ser de 15 minutos'
            })
        
        # Validar formato de color hexadecimal
        if self.color_calendario:
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
    descripcion = models.TextField(
        verbose_name='Descripción',
        help_text='Descripción breve del cubículo',
        blank=True
    )
    numero = models.PositiveSmallIntegerField(
        verbose_name='Número',
        help_text='Número identificador del cubículo',
        null=True,
        blank=True
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
        # Validar capacidad mínima
        if self.capacidad is not None and self.capacidad < 1:
            raise ValidationError({
                'capacidad': 'La capacidad mínima debe ser de 1 persona'
            })
        
        # Validar número positivo
        if self.numero is not None and self.numero < 1:
            raise ValidationError({
                'numero': 'El número del cubículo debe ser mayor a 0'
            })
        
        # Normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip().title()


# Cita model moved/managed in `cit` app; removed duplicate from `clinicas`.
