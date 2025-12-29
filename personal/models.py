"""
Personal app models: Dentista, Disponibilidad, ComisionDentista, ExcepcionDisponibilidad
Moved from cit.models in SOOD-62 refactoring.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from bases.models import ClaseModelo
from clinicas.models import Sucursal

# Forward declarations for circular import handling
# These will be imported from cit at the end after Cita is defined


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
        'cit.Especialidad',
        related_name='dentistas',
        verbose_name='Especialidades',
        help_text='Especialidades que practica el dentista'
    )
    sucursales = models.ManyToManyField(
        Sucursal,
        related_name='dentistas_asignados',
        verbose_name='Sucursales',
        help_text='Sucursales donde el dentista puede atender',
        blank=True
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
        verbose_name='Número de Licencia',
        help_text='Número de licencia para ejercer',
        null=True,
        blank=True
    )
    telefono_movil = models.CharField(
        max_length=20,
        verbose_name='Teléfono Móvil',
        help_text='Número de teléfono móvil personal'
    )
    fecha_contratacion = models.DateField(
        verbose_name='Fecha de Contratación',
        help_text='Fecha en que inició labores',
        null=True,
        blank=True
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
        constraints = [
            models.UniqueConstraint(
                fields=['numero_licencia'],
                name='unique_numero_licencia_personal',
                condition=models.Q(numero_licencia__isnull=False)
            )
        ]
    
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

    def __init__(self, *args, **kwargs):
        # Support legacy constructor kwargs used in tests: 'cedula' -> 'cedula_profesional',
        # 'telefono' -> 'telefono_movil'. Map them before initialization so older tests
        # that pass these names continue to work without changing DB schema.
        if 'cedula' in kwargs and 'cedula_profesional' not in kwargs:
            kwargs['cedula_profesional'] = kwargs.pop('cedula')
        if 'telefono' in kwargs and 'telefono_movil' not in kwargs:
            kwargs['telefono_movil'] = kwargs.pop('telefono')
        super().__init__(*args, **kwargs)
    
    def get_especialidades_nombres(self):
        """Retorna una lista de nombres de especialidades"""
        return ", ".join([esp.nombre for esp in self.especialidades.all()])
    
    get_especialidades_nombres.short_description = 'Especialidades'
    
    def esta_disponible(self, fecha_hora):
        """
        Verifica si el dentista está disponible en una fecha/hora específica.
        Considera:
        1. Disponibilidades configuradas (DisponibilidadDentista)
        2. Excepciones (ExcepcionDisponibilidad)
        3. Horario general de la clínica si no tiene disponibilidades personalizadas
        """
        from datetime import datetime, time
        
        # Obtener día de la semana (0=Lunes, 6=Domingo)
        dia_semana = fecha_hora.weekday()
        hora = fecha_hora.time()
        fecha = fecha_hora.date()
        
        # 1. Verificar excepciones (vacaciones, días libres, etc.)
        excepciones = ExcepcionDisponibilidad.objects.filter(
            dentista=self,
            fecha_inicio__lte=fecha,
            fecha_fin__gte=fecha,
            estado=True
        )
        
        for excepcion in excepciones:
            if excepcion.todo_el_dia:
                return False
            
            if excepcion.hora_inicio and excepcion.hora_fin:
                if excepcion.hora_inicio <= hora < excepcion.hora_fin:
                    return False
        
        # 2. Verificar disponibilidades personalizadas
        disponibilidades = DisponibilidadDentista.objects.filter(
            dentista=self,
            dia_semana=dia_semana,
            activo=True,
            estado=True
        )
        
        if disponibilidades.exists():
            # Tiene horario personalizado, verificar si está dentro de algún rango
            for disp in disponibilidades:
                if disp.hora_inicio <= hora < disp.hora_fin:
                    return True
            return False  # No está en ningún rango de disponibilidad
        
        # 3. Si no tiene disponibilidades personalizadas, usar horario general
        try:
            from cit.models import ConfiguracionClinica
            config = ConfiguracionClinica.objects.filter(estado=True).first()
            if config:
                horario = config.get_horario_dia(dia_semana)
                if horario:
                    hora_inicio, hora_fin = horario
                    return hora_inicio <= hora < hora_fin
                return False  # No se atiende ese día
        except:
            pass
        
        # Por defecto, no disponible
        return False
    
    def get_horarios_semana(self):
        """
        Retorna los horarios de la semana del dentista.
        Formato: {0: [(hora_inicio, hora_fin)], 1: [...], ...}
        """
        horarios = {}
        
        disponibilidades = DisponibilidadDentista.objects.filter(
            dentista=self,
            activo=True,
            estado=True
        ).order_by('dia_semana', 'hora_inicio')
        
        for disp in disponibilidades:
            if disp.dia_semana not in horarios:
                horarios[disp.dia_semana] = []
            horarios[disp.dia_semana].append((disp.hora_inicio, disp.hora_fin))
        
        return horarios


class ComisionDentista(ClaseModelo):
    """
    Modelo para representar las comisiones que recibe un dentista por especialidad.
    Permite configurar comisiones por porcentaje o valor fijo según la especialidad.
    """
    TIPO_COMISION_CHOICES = [
        ('PORCENTAJE', 'Porcentaje (%)'),
        ('FIJO', 'Valor Fijo ($)'),
    ]
    
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name='comisiones',
        verbose_name='Dentista',
        help_text='Dentista al que se le asigna la comisión'
    )
    especialidad = models.ForeignKey(
        'cit.Especialidad',
        on_delete=models.CASCADE,
        related_name='comisiones',
        verbose_name='Especialidad',
        help_text='Especialidad sobre la que se aplica la comisión'
    )
    tipo_comision = models.CharField(
        max_length=10,
        choices=TIPO_COMISION_CHOICES,
        verbose_name='Tipo de Comisión',
        help_text='Tipo de comisión: Porcentaje o Valor Fijo',
        default='PORCENTAJE'
    )
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Porcentaje (%)',
        help_text='Porcentaje de comisión (Ej: 15.50 para 15.50%)',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(100.00)
        ]
    )
    valor_fijo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor Fijo ($)',
        help_text='Valor fijo de comisión por tratamiento (Ej: 50.00)',
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.00)
        ]
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si esta configuración de comisión está activa'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        help_text='Notas adicionales sobre esta comisión',
        blank=True
    )
    
    class Meta:
        verbose_name = 'Comisión de Dentista'
        verbose_name_plural = 'Comisiones de Dentistas'
        ordering = ['dentista', 'especialidad']
        # Removido unique_together para permitir múltiples comisiones (activas/inactivas)
        # La validación de unicidad de comisiones ACTIVAS se maneja en el método clean()
    
    def __str__(self):
        if self.tipo_comision == 'PORCENTAJE':
            return f"{self.dentista} - {self.especialidad}: {self.porcentaje}%"
        else:
            return f"{self.dentista} - {self.especialidad}: ${self.valor_fijo}"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        # Validar que la especialidad esté asignada al dentista
        if self.dentista and self.especialidad:
            if not self.dentista.especialidades.filter(id=self.especialidad.id).exists():
                raise ValidationError({
                    'especialidad': f'El dentista no tiene asignada la especialidad {self.especialidad.nombre}'
                })
        
        # Validar que solo exista UNA comisión activa por dentista+especialidad
        if self.activo and self.dentista and self.especialidad:
            existing = ComisionDentista.objects.filter(
                dentista=self.dentista,
                especialidad=self.especialidad,
                activo=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'activo': f'Ya existe una comisión activa para {self.especialidad.nombre}. '
                             'Debe desactivar la comisión existente antes de activar una nueva.'
                })
        
        # Validar que según el tipo de comisión, solo un campo tenga valor
        if self.tipo_comision == 'PORCENTAJE':
            if not self.porcentaje or self.porcentaje <= 0:
                raise ValidationError({
                    'porcentaje': 'Debe especificar un porcentaje mayor a 0 cuando el tipo es "Porcentaje"'
                })
            # Limpiar valor_fijo si existe
            self.valor_fijo = None
        
        elif self.tipo_comision == 'FIJO':
            if not self.valor_fijo or self.valor_fijo <= 0:
                raise ValidationError({
                    'valor_fijo': 'Debe especificar un valor fijo mayor a 0 cuando el tipo es "Valor Fijo"'
                })
            # Limpiar porcentaje si existe
            self.porcentaje = None
    
    def calcular_comision(self, monto_tratamiento):
        """
        Calcula el monto de comisión basado en el monto del tratamiento.
        
        Args:
            monto_tratamiento (Decimal): Monto total del tratamiento
            
        Returns:
            Decimal: Monto de comisión calculado
        """
        from decimal import Decimal
        
        if not self.activo:
            return Decimal('0.00')
        
        if self.tipo_comision == 'PORCENTAJE':
            if self.porcentaje:
                return (monto_tratamiento * self.porcentaje) / Decimal('100.00')
        elif self.tipo_comision == 'FIJO':
            if self.valor_fijo:
                return self.valor_fijo
        
        return Decimal('0.00')


class DisponibilidadDentista(ClaseModelo):
    """
    Define la disponibilidad horaria de un dentista por día de la semana.
    Permite horarios personalizados por dentista.
    """
    
    # Opciones de días de la semana
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name='disponibilidades',
        verbose_name='Dentista'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='disponibilidades_dentistas',
        verbose_name='Sucursal',
        help_text='Sucursal donde atiende en este horario',
        null=True,
        blank=True
    )
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA,
        verbose_name='Día de la Semana'
    )
    hora_inicio = models.TimeField(
        verbose_name='Hora de Inicio',
        help_text='Hora de inicio de atención'
    )
    hora_fin = models.TimeField(
        verbose_name='Hora de Fin',
        help_text='Hora de fin de atención'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, se usa este horario'
    )
    
    class Meta:
        verbose_name = 'Disponibilidad de Dentista'
        verbose_name_plural = 'Disponibilidades de Dentistas'
        ordering = ['dentista', 'dia_semana', 'hora_inicio']
        unique_together = [['dentista', 'sucursal', 'dia_semana', 'hora_inicio']]
    
    def __str__(self):
        sucursal_str = f" - {self.sucursal.nombre}" if self.sucursal else ""
        return f"{self.dentista} - {self.get_dia_semana_display()}{sucursal_str} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"
    
    def clean(self):
        """Validaciones"""
        from django.core.exceptions import ValidationError
        
        # Validar que hora_inicio y hora_fin tengan valores
        if not self.hora_inicio or not self.hora_fin:
            raise ValidationError({
                'hora_inicio': 'Debe especificar la hora de inicio' if not self.hora_inicio else '',
                'hora_fin': 'Debe especificar la hora de fin' if not self.hora_fin else ''
            })
        
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError({
                'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio'
            })
        
        # Validar que no se solape con otra disponibilidad del mismo dentista en el mismo día y sucursal
        # Solo validar si dentista está definido (necesario para tests de formularios)
        if not self.dentista_id:
            return
            
        filtro = {
            'dentista': self.dentista,
            'dia_semana': self.dia_semana,
            'activo': True
        }
        
        # Si tiene sucursal asignada, validar solo para esa sucursal
        if self.sucursal:
            filtro['sucursal'] = self.sucursal
        
        if self.pk:
            solapamientos = DisponibilidadDentista.objects.filter(**filtro).exclude(pk=self.pk)
        else:
            solapamientos = DisponibilidadDentista.objects.filter(**filtro)
        
        for disp in solapamientos:
            # Verificar solapamiento
            if (self.hora_inicio < disp.hora_fin and self.hora_fin > disp.hora_inicio):
                sucursal_msg = f" en {self.sucursal.nombre}" if self.sucursal else ""
                raise ValidationError(
                    f'Se solapa con otra disponibilidad{sucursal_msg}: {disp.hora_inicio.strftime("%H:%M")} - {disp.hora_fin.strftime("%H:%M")}'
                )


class ExcepcionDisponibilidad(ClaseModelo):
    """
    Define excepciones en la disponibilidad de un dentista.
    Usado para vacaciones, feriados, días libres, etc.
    """
    
    TIPO_CHOICES = [
        ('VACA', 'Vacaciones'),
        ('FERIA', 'Feriado'),
        ('LIBRE', 'Día Libre'),
        ('CAPAC', 'Capacitación'),
        ('OTRO', 'Otro'),
    ]
    
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.CASCADE,
        related_name='excepciones',
        verbose_name='Dentista'
    )
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio'
    )
    fecha_fin = models.DateField(
        verbose_name='Fecha de Fin'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='LIBRE',
        verbose_name='Tipo'
    )
    motivo = models.TextField(
        verbose_name='Motivo',
        help_text='Descripción del motivo de la excepción',
        blank=True
    )
    todo_el_dia = models.BooleanField(
        default=True,
        verbose_name='Todo el Día',
        help_text='Si está marcado, no se atiende en todo el día'
    )
    hora_inicio = models.TimeField(
        verbose_name='Hora de Inicio',
        blank=True,
        null=True,
        help_text='Si no es todo el día, especificar hora de inicio de la excepción'
    )
    hora_fin = models.TimeField(
        verbose_name='Hora de Fin',
        blank=True,
        null=True,
        help_text='Si no es todo el día, especificar hora de fin de la excepción'
    )
    
    class Meta:
        verbose_name = 'Excepción de Disponibilidad'
        verbose_name_plural = 'Excepciones de Disponibilidad'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.dentista} - {self.get_tipo_display()} ({self.fecha_inicio} a {self.fecha_fin})"
    
    def clean(self):
        """Validaciones"""
        from django.core.exceptions import ValidationError
        
        # Solo validar si ambas fechas están presentes
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio > self.fecha_fin:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior o igual a la fecha de inicio'
                })
        
        # Solo validar horas si no es todo el día
        if not self.todo_el_dia:
            if not self.hora_inicio or not self.hora_fin:
                raise ValidationError(
                    'Si no es todo el día, debe especificar hora de inicio y fin'
                )
            
            if self.hora_inicio >= self.hora_fin:
                raise ValidationError({
                    'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio'
                })
