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

# Cita model moved/managed in `cit` app; removed duplicate from `clinicas`.
