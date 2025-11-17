from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
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
        help_text='Nombre completo del contacto'
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono de Emergencia',
        help_text='Teléfono del contacto de emergencia'
    )
    contacto_emergencia_relacion = models.CharField(
        max_length=50,
        verbose_name='Relación',
        help_text='Parentesco o relación (Ej: Madre, Esposo)',
        blank=True
    )
    
    # Relación con Clínica
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.PROTECT,
        related_name='pacientes',
        verbose_name='Clínica',
        help_text='Clínica donde está registrado el paciente'
    )
    
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


class Cita(ClaseModelo):
    """Modelo de Cita Odontológica"""
    
    # Opciones de Estado
    ESTADO_PENDIENTE = 'PEN'
    ESTADO_CONFIRMADA = 'CON'
    ESTADO_EN_ATENCION = 'ATE'
    ESTADO_COMPLETADA = 'COM'
    ESTADO_CANCELADA = 'CAN'
    ESTADO_NO_ASISTIO = 'NAS'
    
    ESTADOS_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_CONFIRMADA, 'Confirmada'),
        (ESTADO_EN_ATENCION, 'En Atención'),
        (ESTADO_COMPLETADA, 'Completada'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_NO_ASISTIO, 'No Asistió'),
    ]
    
    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Paciente',
        help_text='Paciente que tiene la cita'
    )
    dentista = models.ForeignKey(
        Dentista,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Dentista',
        help_text='Dentista que atenderá la cita'
    )
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Especialidad',
        help_text='Especialidad odontológica de la cita'
    )
    cubiculo = models.ForeignKey(
        Cubiculo,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Cubículo',
        help_text='Cubículo donde se realizará la cita'
    )
    
    # Información de la Cita
    fecha_hora = models.DateTimeField(
        verbose_name='Fecha y Hora',
        help_text='Fecha y hora de inicio de la cita'
    )
    duracion = models.PositiveIntegerField(
        verbose_name='Duración (minutos)',
        help_text='Duración estimada en minutos',
        default=30
    )
    estado = models.CharField(
        max_length=3,
        choices=ESTADOS_CHOICES,
        default=ESTADO_PENDIENTE,
        verbose_name='Estado',
        help_text='Estado actual de la cita'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        help_text='Notas u observaciones sobre la cita'
    )
    motivo_cancelacion = models.TextField(
        verbose_name='Motivo de Cancelación',
        blank=True,
        help_text='Razón por la cual se canceló la cita'
    )
    
    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['fecha_hora', 'estado']),
            models.Index(fields=['dentista', 'fecha_hora']),
            models.Index(fields=['paciente', 'fecha_hora']),
        ]
    
    def __str__(self):
        return f"{self.paciente.get_nombre_completo()} - {self.especialidad.nombre} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        from datetime import datetime, timedelta
        
        errors = {}
        
        # Acceder a relaciones de forma segura usando _id o hasattr
        dentista_id = self.dentista_id
        cubiculo_id = self.cubiculo_id
        especialidad_id = self.especialidad_id
        
        # Cargar objetos solo si están guardados
        try:
            dentista = self.dentista if dentista_id else None
        except Cita.dentista.RelatedObjectDoesNotExist:
            dentista = None
            
        try:
            cubiculo = self.cubiculo if cubiculo_id else None
        except Cita.cubiculo.RelatedObjectDoesNotExist:
            cubiculo = None
            
        try:
            especialidad = self.especialidad if especialidad_id else None
        except Cita.especialidad.RelatedObjectDoesNotExist:
            especialidad = None
        
        # Validación 1: No solapamiento por dentista
        if dentista and self.fecha_hora and self.duracion:
            fecha_fin = self.fecha_hora + timedelta(minutes=self.duracion)
            
            # Buscar citas del mismo dentista que se solapen
            citas_solapadas_dentista = Cita.objects.filter(
                dentista=dentista,
                fecha_hora__lt=fecha_fin,
                estado__in=[self.ESTADO_PENDIENTE, self.ESTADO_CONFIRMADA, self.ESTADO_EN_ATENCION]
            ).exclude(pk=self.pk)
            
            for cita in citas_solapadas_dentista:
                cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
                if cita.fecha_hora < fecha_fin and cita_fin > self.fecha_hora:
                    errors['dentista'] = f'El dentista {dentista} ya tiene una cita programada entre {cita.fecha_hora.strftime("%H:%M")} y {cita_fin.strftime("%H:%M")}'
                    break
        
        # Validación 2: No solapamiento por cubículo
        if cubiculo and self.fecha_hora and self.duracion:
            fecha_fin = self.fecha_hora + timedelta(minutes=self.duracion)
            
            citas_solapadas_cubiculo = Cita.objects.filter(
                cubiculo=cubiculo,
                fecha_hora__lt=fecha_fin,
                estado__in=[self.ESTADO_PENDIENTE, self.ESTADO_CONFIRMADA, self.ESTADO_EN_ATENCION]
            ).exclude(pk=self.pk)
            
            for cita in citas_solapadas_cubiculo:
                cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
                if cita.fecha_hora < fecha_fin and cita_fin > self.fecha_hora:
                    errors['cubiculo'] = f'El cubículo {cubiculo} ya está ocupado entre {cita.fecha_hora.strftime("%H:%M")} y {cita_fin.strftime("%H:%M")}'
                    break
        
        # Validación 3: Dentista tiene la especialidad
        if dentista and especialidad:
            if not dentista.especialidades.filter(pk=especialidad.pk).exists():
                errors['especialidad'] = f'El dentista {dentista} no tiene la especialidad {especialidad.nombre}'
        
        # Validación 4: Cubículo pertenece a la sucursal del dentista
        if dentista and cubiculo:
            if dentista.sucursal_principal and cubiculo.sucursal != dentista.sucursal_principal:
                errors['cubiculo'] = f'El cubículo debe pertenecer a la sucursal {dentista.sucursal_principal.nombre} del dentista'
        
        # Validación 5: Domingos requieren confirmación
        if self.fecha_hora:
            if self.fecha_hora.weekday() == 6:  # 6 = Domingo
                if self.estado == self.ESTADO_PENDIENTE:
                    errors['fecha_hora'] = 'Las citas en domingo deben estar confirmadas. No se pueden crear citas pendientes los domingos.'
        
        if errors:
            raise ValidationError(errors)
    
    def get_duracion_display_horas(self):
        """Retorna la duración en formato horas:minutos"""
        horas = self.duracion // 60
        minutos = self.duracion % 60
        if horas > 0:
            return f"{horas}h {minutos}min" if minutos > 0 else f"{horas}h"
        return f"{minutos}min"
    
    get_duracion_display_horas.short_description = 'Duración'
    
    def get_estado_badge(self):
        """Retorna el estado con formato de badge para templates"""
        estados_colores = {
            self.ESTADO_PENDIENTE: 'warning',
            self.ESTADO_CONFIRMADA: 'info',
            self.ESTADO_EN_ATENCION: 'primary',
            self.ESTADO_COMPLETADA: 'success',
            self.ESTADO_CANCELADA: 'danger',
            self.ESTADO_NO_ASISTIO: 'secondary',
        }
        return {
            'estado': self.get_estado_display(),
            'color': estados_colores.get(self.estado, 'secondary')
        }
    
    def puede_cancelar(self):
        """Verifica si la cita puede ser cancelada"""
        return self.estado in [self.ESTADO_PENDIENTE, self.ESTADO_CONFIRMADA]
    
    def puede_confirmar(self):
        """Verifica si la cita puede ser confirmada"""
        return self.estado == self.ESTADO_PENDIENTE
    
    def puede_iniciar_atencion(self):
        """Verifica si la cita puede iniciar atención"""
        return self.estado in [self.ESTADO_CONFIRMADA, self.ESTADO_PENDIENTE]


# ============================================================================
# MODELOS DE CONFIGURACIÓN Y DISPONIBILIDAD
# ============================================================================

class ConfiguracionClinica(ClaseModelo):
    """
    Configuración global de la clínica.
    Solo debe existir un registro (Singleton pattern).
    """
    sucursal = models.OneToOneField(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='configuracion',
        verbose_name='Sucursal',
        help_text='Sucursal a la que aplica esta configuración'
    )
    
    # Horarios de atención generales
    horario_inicio = models.TimeField(
        default='08:30:00',
        verbose_name='Hora de Inicio',
        help_text='Hora de inicio de atención (ej: 08:30)'
    )
    horario_fin = models.TimeField(
        default='18:00:00',
        verbose_name='Hora de Fin',
        help_text='Hora límite para iniciar última cita (ej: 18:00)'
    )
    
    # Duración de slots en el calendario
    duracion_slot = models.PositiveIntegerField(
        default=30,
        verbose_name='Duración de Slot (minutos)',
        help_text='Intervalo de tiempo en el calendario (15, 30, 60 minutos)'
    )
    
    # Días laborables
    atiende_lunes = models.BooleanField(default=True, verbose_name='Lunes')
    atiende_martes = models.BooleanField(default=True, verbose_name='Martes')
    atiende_miercoles = models.BooleanField(default=True, verbose_name='Miércoles')
    atiende_jueves = models.BooleanField(default=True, verbose_name='Jueves')
    atiende_viernes = models.BooleanField(default=True, verbose_name='Viernes')
    atiende_sabado = models.BooleanField(default=False, verbose_name='Sábado')
    atiende_domingo = models.BooleanField(default=False, verbose_name='Domingo')
    
    # Horario especial sábado
    sabado_hora_inicio = models.TimeField(
        default='08:30:00',
        verbose_name='Sábado - Hora Inicio',
        blank=True,
        null=True
    )
    sabado_hora_fin = models.TimeField(
        default='12:00:00',
        verbose_name='Sábado - Hora Fin',
        blank=True,
        null=True
    )
    
    # Citas el mismo día
    permitir_citas_mismo_dia = models.BooleanField(
        default=True,
        verbose_name='Permitir Citas el Mismo Día',
        help_text='Si está habilitado, se pueden agendar citas para el día actual'
    )
    horas_anticipacion_minima = models.PositiveIntegerField(
        default=0,
        verbose_name='Horas de Anticipación Mínima',
        help_text='Horas mínimas de anticipación para agendar (0 = inmediato)'
    )
    
    class Meta:
        verbose_name = 'Configuración de Clínica'
        verbose_name_plural = 'Configuraciones de Clínica'
    
    def __str__(self):
        return f"Configuración - {self.sucursal.nombre}"
    
    def clean(self):
        """Validaciones"""
        from django.core.exceptions import ValidationError
        
        if self.horario_inicio >= self.horario_fin:
            raise ValidationError({
                'horario_fin': 'La hora de fin debe ser posterior a la hora de inicio'
            })
        
        if self.duracion_slot not in [15, 30, 60]:
            raise ValidationError({
                'duracion_slot': 'La duración del slot debe ser 15, 30 o 60 minutos'
            })
        
        if self.atiende_sabado and self.sabado_hora_inicio and self.sabado_hora_fin:
            if self.sabado_hora_inicio >= self.sabado_hora_fin:
                raise ValidationError({
                    'sabado_hora_fin': 'La hora de fin del sábado debe ser posterior a la hora de inicio'
                })
    
    def get_dias_atencion(self):
        """Retorna lista de días de la semana que se atiende (0=Lunes, 6=Domingo)"""
        dias = []
        if self.atiende_lunes: dias.append(0)
        if self.atiende_martes: dias.append(1)
        if self.atiende_miercoles: dias.append(2)
        if self.atiende_jueves: dias.append(3)
        if self.atiende_viernes: dias.append(4)
        if self.atiende_sabado: dias.append(5)
        if self.atiende_domingo: dias.append(6)
        return dias
    
    def get_horario_dia(self, dia_semana):
        """
        Retorna el horario para un día específico.
        dia_semana: 0=Lunes, 1=Martes, ..., 6=Domingo
        Retorna: (hora_inicio, hora_fin) o None si no atiende
        """
        dias_atiende = self.get_dias_atencion()
        
        if dia_semana not in dias_atiende:
            return None
        
        # Horario especial para sábado
        if dia_semana == 5 and self.sabado_hora_inicio and self.sabado_hora_fin:
            return (self.sabado_hora_inicio, self.sabado_hora_fin)
        
        return (self.horario_inicio, self.horario_fin)


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

