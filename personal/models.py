"""
Personal app models: Dentista, Disponibilidad, ComisionDentista, ExcepcionDisponibilidad
Moved from cit.models in SOOD-62 refactoring.
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from bases.models import ClaseModelo
from clinicas.models import Sucursal, Especialidad

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
        Especialidad,
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
        null=True,
        blank=True,
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
        null=True,
        blank=True,
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
        Especialidad,
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


class Personal(ClaseModelo):
    """
    Modelo para personal administrativo/auxiliar/servicios.
    Similar a Dentista pero sin comisiones.
    """
    TIPO_PERSONAL = [
        ('administrativo', 'Administrativo'),
        ('auxiliar', 'Auxiliar'),
        ('asistente', 'Asistente'),
        ('recepcion', 'Recepción'),
        ('servicios', 'Servicios Generales'),
    ]

    TIPO_COMPENSACION = [
        ('MENSUAL', 'Mensual (Salario fijo)'),
        ('POR_HORA', 'Pago por hora'),
        ('POR_DIA', 'Pago por día'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='personal_profile',
        verbose_name='Usuario',
        help_text='Usuario del sistema asociado al personal'
    )
    tipo_personal = models.CharField(
        max_length=20,
        choices=TIPO_PERSONAL,
        default='auxiliar',
        verbose_name='Tipo de Personal'
    )
    sucursales = models.ManyToManyField(
        Sucursal,
        related_name='personal_asignado',
        verbose_name='Sucursales',
        help_text='Sucursales donde puede trabajar',
        blank=True
    )
    sucursal_principal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personal_principal',
        verbose_name='Sucursal Principal'
    )
    tipo_compensacion = models.CharField(
        max_length=10,
        choices=TIPO_COMPENSACION,
        default='MENSUAL',
        verbose_name='Tipo de Compensación'
    )
    salario_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('482.00'),
        verbose_name='Salario Mensual',
        help_text='Salario mensual (SBU por defecto)'
    )
    tarifa_por_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Tarifa por Hora',
        help_text='Usar si la compensación es por hora'
    )
    tarifa_por_dia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Tarifa por Día',
        help_text='Usar si la compensación es por día'
    )
    fecha_contratacion = models.DateField(
        verbose_name='Fecha de Contratación',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Personal'
        verbose_name_plural = 'Personal'
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

    def get_tarifa_hora_base(self):
        """
        Calcula la tarifa hora base.
        Regla: salario mensual / 240 (30 días * 8 horas).
        """
        if self.tipo_compensacion == 'POR_HORA' and self.tarifa_por_hora:
            return self.tarifa_por_hora
        if self.tipo_compensacion == 'POR_DIA' and self.tarifa_por_dia:
            return (self.tarifa_por_dia / Decimal('8')).quantize(Decimal('0.01'))
        return (self.salario_mensual / Decimal('240')).quantize(Decimal('0.01'))


class RegistroHorasPersonal(ClaseModelo):
    """
    Registro de horas extra del personal (solo horas extra).
    """
    TIPO_EXTRA = [
        ('RECARGO_25', 'Extra 25% (después de 18:00)'),
        ('RECARGO_50', 'Extra 50% (después de 20:00)'),
        ('RECARGO_100', 'Extra 100% (feriados/domingo)'),
        ('SABADO_MEDIO_DIA', 'Sábado medio día (USD 20)'),
    ]

    ESTADO = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name='horas_extra',
        verbose_name='Personal'
    )
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora Inicio')
    hora_fin = models.TimeField(verbose_name='Hora Fin')
    tipo_extra = models.CharField(
        max_length=20,
        choices=TIPO_EXTRA,
        default='RECARGO_25',
        verbose_name='Tipo de Extra'
    )
    horas = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Horas'
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Valor Total'
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    aprobado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aprobaciones_horas_personal',
        verbose_name='Aprobado por'
    )
    aprobado_en = models.DateTimeField(null=True, blank=True, verbose_name='Aprobado en')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    es_desglosado = models.BooleanField(
        default=False,
        verbose_name='Es Desglosado',
        help_text='True si este registro fue creado automáticamente por desglose de tiempo nocturno'
    )
    registro_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='registros_desglosados',
        verbose_name='Registro Padre',
        help_text='Registro original si este fue desglosado automáticamente'
    )

    class Meta:
        verbose_name = 'Registro de Horas Extra'
        verbose_name_plural = 'Registros de Horas Extra'
        ordering = ['-fecha', 'personal']

    def __str__(self):
        return f"{self.personal} - {self.fecha} ({self.get_tipo_extra_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        # Validar que la hora de fin sea posterior a la hora de inicio
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio')
        
        # Verificar conflictos de horarios para el mismo personal en la misma fecha
        if self.fecha and self.hora_inicio and self.hora_fin:
            from datetime import datetime, time
            
            # No buscar conflictos si es un registro desglosado (hijo)
            # solo si es el registro principal
            if not self.es_desglosado:
                # Buscar registros conflictivos del mismo personal en la misma fecha
                conflictos = RegistroHorasPersonal.objects.filter(
                    personal=self.personal,
                    fecha=self.fecha,
                    estado='PENDIENTE'  # Solo verificar pendientes
                )
                
                # Si es una actualización, excluir el registro actual
                if self.pk:
                    conflictos = conflictos.exclude(pk=self.pk)
                
                for reg in conflictos:
                    # Verificar si hay superposición de horarios
                    if self._horarios_se_superponen(self.hora_inicio, self.hora_fin, reg.hora_inicio, reg.hora_fin):
                        raise ValidationError(
                            f'Ya existe un registro de horas extra para el {self.fecha.strftime("%d/%m/%Y")} '
                            f'en el horario {reg.hora_inicio.strftime("%H:%M")} - {reg.hora_fin.strftime("%H:%M")}. '
                            f'No se pueden crear registros con horarios conflictivos.'
                        )

    def save(self, *args, **kwargs):
        from datetime import datetime
        from django.utils import timezone
    
    @staticmethod
    def _horarios_se_superponen(inicio1, fin1, inicio2, fin2):
        """
        Verifica si dos rangos de tiempo se superponen.
        """
        # Los rangos se superponen si:
        # inicio1 < fin2 AND inicio2 < fin1
        return inicio1 < fin2 and inicio2 < fin1
        if self.hora_inicio and self.hora_fin:
            dt_inicio = datetime.combine(self.fecha, self.hora_inicio)
            dt_fin = datetime.combine(self.fecha, self.hora_fin)
            delta = dt_fin - dt_inicio
            self.horas = Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.01'))

        if self.tipo_extra == 'SABADO_MEDIO_DIA':
            self.valor_total = Decimal('20.00')
            if self.horas == Decimal('0.00'):
                self.horas = Decimal('4.00')
        else:
            tarifa_base = self.personal.get_tarifa_hora_base()
            if self.tipo_extra == 'RECARGO_25':
                factor = Decimal('1.25')
            elif self.tipo_extra == 'RECARGO_50':
                factor = Decimal('1.50')
            elif self.tipo_extra == 'RECARGO_100':
                factor = Decimal('2.00')
            else:
                factor = Decimal('1.00')
            self.valor_total = (tarifa_base * factor * self.horas).quantize(Decimal('0.01'))

        if self.estado == 'APROBADO' and not self.aprobado_en:
            self.aprobado_en = timezone.now()

        super().save(*args, **kwargs)

    @staticmethod
    def desglosa_horas_nocturnas(personal, fecha, hora_inicio, hora_fin, observaciones=''):
        """
        Analiza un período de horas y lo desglose automáticamente si cruza las 20:00.
        Retorna una lista de tuplas: (tipo_extra, horas_inicio, horas_fin)
        
        Lógica:
        - 18:00 a 20:00: RECARGO_25 (25%)
        - 20:00 en adelante: RECARGO_50 (50%) - HORAS NOCTURNAS
        - Domingo/feriado: RECARGO_100 (100%)
        """
        from datetime import datetime, time
        
        HORA_LIMITE_NOCTURNO = time(20, 0)  # 20:00 es el límite
        
        # Convertir a datetime para comparación
        dt_inicio = datetime.combine(fecha, hora_inicio)
        dt_fin = datetime.combine(fecha, hora_fin)
        
        # Si el período no cruza las 20:00, retornar sin desglose
        if hora_fin <= HORA_LIMITE_NOCTURNO:
            return [(dt_inicio, dt_fin, 'RECARGO_25')]
        
        if hora_inicio >= HORA_LIMITE_NOCTURNO:
            return [(dt_inicio, dt_fin, 'RECARGO_50')]
        
        # El período cruza las 20:00, crear dos registros
        dt_limite = datetime.combine(fecha, HORA_LIMITE_NOCTURNO)
        
        registros = [
            (dt_inicio, dt_limite, 'RECARGO_25'),      # Antes de 20:00 = 25%
            (dt_limite, dt_fin, 'RECARGO_50'),          # Después de 20:00 = 50% (nocturno)
        ]
        
        return registros

    @classmethod
    def crear_con_desglose(cls, personal, fecha, hora_inicio, hora_fin, observaciones='', uc=None):
        """
        Crea registro(s) de horas extra con desglose automático si es necesario.
        Retorna una lista de registros creados.
        """
        from datetime import time
        
        registros_creados = []
        desglose = cls.desglosa_horas_nocturnas(personal, fecha, hora_inicio, hora_fin, observaciones)
        
        # Caso 1: Sin desglose (período simple)
        if len(desglose) == 1:
            dt_inicio, dt_fin, tipo_extra = desglose[0]
            registro = cls(
                personal=personal,
                fecha=fecha,
                hora_inicio=dt_inicio.time(),
                hora_fin=dt_fin.time(),
                tipo_extra=tipo_extra,
                observaciones=observaciones,
                es_desglosado=False,
                uc=uc
            )
            registro.save()
            registros_creados.append(registro)
        
        # Caso 2: Con desglose (período cruza 20:00)
        else:
            # Crear registro padre
            registro_padre = cls(
                personal=personal,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                tipo_extra='RECARGO_25',  # Será virtual, solo para referencia
                observaciones=f"{observaciones} [PERÍODO COMPLETO: {hora_inicio}-{hora_fin}]" if observaciones else f"[PERÍODO COMPLETO: {hora_inicio}-{hora_fin}]",
                es_desglosado=False,
                uc=uc
            )
            registro_padre.save()
            
            # Crear registros desglosados
            for i, (dt_inicio, dt_fin, tipo_extra) in enumerate(desglose):
                registro_desglosado = cls(
                    personal=personal,
                    fecha=fecha,
                    hora_inicio=dt_inicio.time(),
                    hora_fin=dt_fin.time(),
                    tipo_extra=tipo_extra,
                    observaciones=observaciones,
                    es_desglosado=True,
                    registro_padre=registro_padre,
                    uc=uc
                )
                registro_desglosado.save()
                registros_creados.append(registro_desglosado)
        
        return registros_creados


class ExcepcionPersonal(ClaseModelo):
    """
    Excepciones de jornada del personal (vacaciones, permisos, capacitaciones).
    """
    TIPO_EXCEPCION = [
        ('VACACIONES', 'Vacaciones'),
        ('PERMISO', 'Permiso'),
        ('CAPACITACION', 'Capacitación'),
        ('OTRO', 'Otro'),
    ]

    personal = models.ForeignKey(
        Personal,
        on_delete=models.CASCADE,
        related_name='excepciones',
        verbose_name='Personal'
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin')
    tipo = models.CharField(max_length=15, choices=TIPO_EXCEPCION, default='PERMISO')
    motivo = models.TextField(blank=True, verbose_name='Motivo')

    class Meta:
        verbose_name = 'Excepción de Personal'
        verbose_name_plural = 'Excepciones de Personal'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.personal} - {self.get_tipo_display()}"
