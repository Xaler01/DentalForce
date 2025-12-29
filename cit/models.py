from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from bases.models import ClaseModelo

# Clinica and Sucursal are canonical models defined in the `clinicas` app.
# Import them here so the `cit` module exposes the same classes and avoids
# duplicate model definitions and DB/table mismatches.
from clinicas.models import Clinica, Sucursal  # noqa: F401

# Paciente is canonical model defined in the `pacientes` app.
# Import it here for backward compatibility with code that uses cit.models.Paciente
from pacientes.models import Paciente  # noqa: F401

# Dentista and related models moved to `personal` app in SOOD-62 refactoring.
# Import them here for backward compatibility.
from personal.models import (  # noqa: F401
    Dentista,
    ComisionDentista,
    DisponibilidadDentista,
    ExcepcionDisponibilidad,
)

# Create other models here.

# `Clinica` and `Sucursal` are defined in the `clinicas` app and imported
# above. Keep the canonical models in `clinicas.models` to avoid duplicate
# definitions and DB/table mismatches.


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


# Dentista and related models moved to personal.models (SOOD-62 refactoring)

# Paciente model moved to pacientes.models (SOOD-62 refactoring)

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
        return f"Cita #{self.id} - {self.paciente} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
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
                    # Reportar como error no relacionado a un campo concreto para
                    # evitar ValueError en formularios que no exponen `fecha_hora`.
                    errors['__all__'] = 'Las citas en domingo deben estar confirmadas. No se pueden crear citas pendientes los domingos.'
        
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


# DisponibilidadDentista and ExcepcionDisponibilidad moved to personal.models (SOOD-62 refactoring)

