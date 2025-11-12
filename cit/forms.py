from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Cita, Dentista, Especialidad, Cubiculo


class CitaForm(forms.ModelForm):
    """
    Formulario para crear y editar citas.
    Incluye validaciones de negocio y widgets personalizados.
    """
    
    class Meta:
        model = Cita
        fields = [
            'paciente', 
            'dentista', 
            'especialidad', 
            'cubiculo',
            'fecha_hora', 
            'duracion', 
            'estado',
            'observaciones'
        ]
        widgets = {
            'paciente': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'dentista': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'especialidad': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'cubiculo': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'fecha_hora': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': True
            }, format='%Y-%m-%dT%H:%M'),
            'duracion': forms.Select(
                choices=[
                    (15, '15 minutos'),
                    (30, '30 minutos'),
                    (45, '45 minutos'),
                    (60, '1 hora'),
                    (90, '1 hora 30 minutos'),
                    (120, '2 horas'),
                ],
                attrs={
                    'class': 'form-control',
                    'required': True
                }
            ),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales sobre la cita...'
            }),
        }
        labels = {
            'paciente': 'Paciente',
            'dentista': 'Dentista',
            'especialidad': 'Especialidad',
            'cubiculo': 'Cubículo',
            'fecha_hora': 'Fecha y Hora',
            'duracion': 'Duración',
            'estado': 'Estado',
            'observaciones': 'Observaciones',
        }
        help_texts = {
            'fecha_hora': 'Seleccione la fecha y hora de la cita',
            'duracion': 'Duración estimada de la cita',
            'observaciones': 'Información adicional relevante para la cita',
        }
    
    def __init__(self, *args, **kwargs):
        """Personalizar inicialización del formulario"""
        super().__init__(*args, **kwargs)
        
        # Configurar formato de entrada para datetime-local
        self.fields['fecha_hora'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Si es edición, deshabilitar campos según el estado
        if self.instance.pk:
            estado = self.instance.estado
            
            # Si la cita está completada o cancelada, solo permitir editar observaciones
            if estado in [Cita.ESTADO_COMPLETADA, Cita.ESTADO_CANCELADA, Cita.ESTADO_NO_ASISTIO]:
                for field_name in ['paciente', 'dentista', 'especialidad', 'cubiculo', 'fecha_hora', 'duracion']:
                    self.fields[field_name].disabled = True
            
            # Si la cita está en atención, no permitir cambiar paciente, dentista, especialidad
            elif estado == Cita.ESTADO_EN_ATENCION:
                for field_name in ['paciente', 'dentista', 'especialidad']:
                    self.fields[field_name].disabled = True
    
    def clean_fecha_hora(self):
        """Validar que la fecha y hora de la cita sea válida"""
        from .models import ConfiguracionClinica
        
        fecha_hora = self.cleaned_data.get('fecha_hora')
        
        if not fecha_hora:
            raise ValidationError('Debe seleccionar una fecha y hora para la cita')
        
        ahora = timezone.now()
        
        # Para ediciones, permitir si la fecha no cambió
        if self.instance.pk:
            if self.instance.fecha_hora == fecha_hora:
                return fecha_hora
        
        # Obtener configuración de la clínica
        config = ConfiguracionClinica.objects.filter(estado=True).first()
        
        if not config:
            # Si no hay configuración, usar validación por defecto
            if fecha_hora < ahora:
                raise ValidationError('La fecha y hora de la cita no puede ser en el pasado')
        else:
            # Validar citas el mismo día según configuración
            if config.permitir_citas_mismo_dia:
                # Validar horas de anticipación mínima
                if config.horas_anticipacion_minima > 0:
                    anticipacion_minima = ahora + timedelta(hours=config.horas_anticipacion_minima)
                    if fecha_hora < anticipacion_minima:
                        raise ValidationError(
                            f'Debe agendar con al menos {config.horas_anticipacion_minima} hora(s) de anticipación'
                        )
                else:
                    # Permitir inmediato, solo validar que no sea en el pasado
                    if fecha_hora < ahora:
                        raise ValidationError('La fecha y hora de la cita no puede ser en el pasado')
            else:
                # No se permiten citas el mismo día
                if fecha_hora.date() <= ahora.date():
                    raise ValidationError('No se permiten citas para el día de hoy. Debe agendar para mañana o después.')
        
        # Validar que no sea más de 6 meses en el futuro
        seis_meses = ahora + timedelta(days=180)
        if fecha_hora > seis_meses:
            raise ValidationError('La cita no puede ser programada con más de 6 meses de anticipación')
        
        # Validar horario de atención según configuración
        if config:
            hora = fecha_hora.time()
            dia_semana = fecha_hora.weekday()
            
            horario = config.get_horario_dia(dia_semana)
            if not horario:
                dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                raise ValidationError(
                    f'No se atiende los días {dias[dia_semana]}'
                )
            
            hora_apertura, hora_cierre = horario
            
            if hora < hora_apertura or hora >= hora_cierre:
                raise ValidationError(
                    f'Las citas solo pueden agendarse entre {hora_apertura.strftime("%H:%M")} '
                    f'y {hora_cierre.strftime("%H:%M")}'
                )
        else:
            # Validación por defecto
            hora = fecha_hora.time()
            hora_apertura = datetime.strptime('08:00', '%H:%M').time()
            hora_cierre = datetime.strptime('20:00', '%H:%M').time()
            
            if hora < hora_apertura or hora >= hora_cierre:
                raise ValidationError(
                    f'Las citas solo pueden agendarse entre {hora_apertura.strftime("%H:%M")} '
                    f'y {hora_cierre.strftime("%H:%M")}'
                )
        
        return fecha_hora
    
    def clean_duracion(self):
        """Validar la duración de la cita"""
        duracion = self.cleaned_data.get('duracion')
        
        if not duracion:
            raise ValidationError('Debe seleccionar una duración para la cita')
        
        if duracion < 15:
            raise ValidationError('La duración mínima de una cita es 15 minutos')
        
        if duracion > 240:
            raise ValidationError('La duración máxima de una cita es 4 horas (240 minutos)')
        
        return duracion
    
    def clean_dentista(self):
        """Validar que el dentista esté activo"""
        dentista = self.cleaned_data.get('dentista')
        
        if dentista and not dentista.estado:
            raise ValidationError('El dentista seleccionado no está activo')
        
        return dentista
    
    def clean_especialidad(self):
        """Validar que la especialidad esté activa"""
        especialidad = self.cleaned_data.get('especialidad')
        
        if especialidad and not especialidad.estado:
            raise ValidationError('La especialidad seleccionada no está activa')
        
        return especialidad
    
    def clean_cubiculo(self):
        """Validar que el cubículo esté activo"""
        cubiculo = self.cleaned_data.get('cubiculo')
        
        if cubiculo and not cubiculo.estado:
            raise ValidationError('El cubículo seleccionado no está activo')
        
        return cubiculo
    
    def clean(self):
        """Validaciones que requieren múltiples campos"""
        cleaned_data = super().clean()
        
        dentista = cleaned_data.get('dentista')
        especialidad = cleaned_data.get('especialidad')
        cubiculo = cleaned_data.get('cubiculo')
        fecha_hora = cleaned_data.get('fecha_hora')
        duracion = cleaned_data.get('duracion')
        estado = cleaned_data.get('estado')
        
        # Solo validar si todos los campos necesarios están presentes
        if not all([dentista, especialidad, cubiculo, fecha_hora, duracion]):
            return cleaned_data
        
        # ========================================================================
        # VALIDACIÓN 1: Dentista tiene la especialidad
        # ========================================================================
        if especialidad not in dentista.especialidades.all():
            raise ValidationError({
                'especialidad': f'El Dr./Dra. {dentista} no tiene certificación en {especialidad}'
            })
        
        # ========================================================================
        # VALIDACIÓN 2: Cubículo pertenece a la sucursal del dentista
        # ========================================================================
        if dentista.sucursal_principal and cubiculo.sucursal != dentista.sucursal_principal:
            raise ValidationError({
                'cubiculo': f'El cubículo debe pertenecer a la sucursal {dentista.sucursal_principal}'
            })
        
        # ========================================================================
        # VALIDACIÓN 3: Horario laboral extendido
        # ========================================================================
        # Validar que la cita termine antes del cierre (20:00)
        fecha_fin = fecha_hora + timedelta(minutes=duracion)
        hora_cierre = datetime.strptime('20:00', '%H:%M').time()
        
        if fecha_fin.time() > hora_cierre:
            raise ValidationError({
                'duracion': f'La cita terminaría a las {fecha_fin.strftime("%H:%M")}, '
                           f'después del horario de cierre (20:00). '
                           f'Ajuste la hora de inicio o la duración.'
            })
        
        # ========================================================================
        # VALIDACIÓN 4: Disponibilidad del dentista (evitar solapamientos)
        # ========================================================================
        citas_dentista = Cita.objects.filter(
            dentista=dentista,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=self.instance.pk if self.instance.pk else None)
        
        for cita in citas_dentista:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            # Verificar si hay solapamiento
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                raise ValidationError({
                    'fecha_hora': f'El Dr./Dra. {dentista} ya tiene una cita programada en este horario. '
                                  f'Cita existente: {cita.fecha_hora.strftime("%d/%m/%Y %H:%M")} - '
                                  f'{cita_fin.strftime("%H:%M")} con {cita.paciente}'
                })
        
        # ========================================================================
        # VALIDACIÓN 5: Disponibilidad del cubículo (evitar solapamientos)
        # ========================================================================
        citas_cubiculo = Cita.objects.filter(
            cubiculo=cubiculo,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=self.instance.pk if self.instance.pk else None)
        
        for cita in citas_cubiculo:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            # Verificar si hay solapamiento
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                raise ValidationError({
                    'cubiculo': f'El cubículo {cubiculo} ya está ocupado en este horario. '
                                f'Cita existente: {cita.fecha_hora.strftime("%d/%m/%Y %H:%M")} - '
                                f'{cita_fin.strftime("%H:%M")} (Dr./Dra. {cita.dentista})'
                })
        
        # ========================================================================
        # VALIDACIÓN 6: Límite de citas por día para el paciente
        # ========================================================================
        paciente = cleaned_data.get('paciente')
        if paciente and fecha_hora:
            # Contar citas del mismo día
            inicio_dia = fecha_hora.replace(hour=0, minute=0, second=0, microsecond=0)
            fin_dia = inicio_dia + timedelta(days=1)
            
            citas_dia = Cita.objects.filter(
                paciente=paciente,
                fecha_hora__gte=inicio_dia,
                fecha_hora__lt=fin_dia,
                estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if citas_dia.count() >= 3:
                raise ValidationError({
                    'paciente': f'{paciente} ya tiene 3 citas programadas para el {fecha_hora.strftime("%d/%m/%Y")}. '
                                f'Límite máximo alcanzado.'
                })
        
        # ========================================================================
        # VALIDACIÓN 7: Validar transiciones de estado (solo en edición)
        # ========================================================================
        if self.instance.pk and estado:
            estado_anterior = self.instance.estado
            
            # Definir transiciones permitidas
            transiciones_permitidas = {
                Cita.ESTADO_PENDIENTE: [Cita.ESTADO_CONFIRMADA, Cita.ESTADO_CANCELADA],
                Cita.ESTADO_CONFIRMADA: [Cita.ESTADO_EN_ATENCION, Cita.ESTADO_CANCELADA, Cita.ESTADO_NO_ASISTIO],
                Cita.ESTADO_EN_ATENCION: [Cita.ESTADO_COMPLETADA],
                Cita.ESTADO_COMPLETADA: [],  # Estado final
                Cita.ESTADO_CANCELADA: [],   # Estado final
                Cita.ESTADO_NO_ASISTIO: [],  # Estado final
            }
            
            if estado != estado_anterior:
                if estado not in transiciones_permitidas.get(estado_anterior, []):
                    raise ValidationError({
                        'estado': f'No se puede cambiar de "{self.instance.get_estado_display()}" '
                                  f'a "{dict(Cita.ESTADOS_CHOICES)[estado]}". Transición no permitida.'
                    })
        
        # ========================================================================
        # VALIDACIÓN 8: Citas en domingo requieren confirmación previa
        # ========================================================================
        if fecha_hora.weekday() == 6:  # 6 = domingo
            if estado == Cita.ESTADO_PENDIENTE and not self.instance.pk:
                raise ValidationError({
                    'estado': 'Las citas programadas para domingo deben estar confirmadas desde su creación. '
                              'Cambie el estado a "Confirmada".'
                })
        
        # ========================================================================
        # VALIDACIÓN 9: No permitir editar citas en estado final
        # ========================================================================
        if self.instance.pk:
            if self.instance.estado in [Cita.ESTADO_COMPLETADA, Cita.ESTADO_CANCELADA, Cita.ESTADO_NO_ASISTIO]:
                # Verificar si se están cambiando campos críticos
                campos_criticos = ['paciente', 'dentista', 'especialidad', 'cubiculo', 'fecha_hora', 'duracion']
                for campo in campos_criticos:
                    valor_original = getattr(self.instance, campo)
                    valor_nuevo = cleaned_data.get(campo)
                    if valor_original != valor_nuevo:
                        raise ValidationError(
                            f'No se puede modificar una cita en estado "{self.instance.get_estado_display()}". '
                            f'Solo puede editar las observaciones.'
                        )
        
        return cleaned_data


class CitaCancelForm(forms.ModelForm):
    """
    Formulario para cancelar una cita.
    Solo requiere el motivo de cancelación.
    """
    
    class Meta:
        model = Cita
        fields = ['motivo_cancelacion']
        widgets = {
            'motivo_cancelacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Por favor, indique el motivo de la cancelación...',
                'required': True
            })
        }
        labels = {
            'motivo_cancelacion': 'Motivo de Cancelación'
        }
    
    def clean_motivo_cancelacion(self):
        """Validar que se proporcione un motivo"""
        motivo = self.cleaned_data.get('motivo_cancelacion')
        
        if not motivo or len(motivo.strip()) < 10:
            raise ValidationError('Debe proporcionar un motivo de cancelación de al menos 10 caracteres')
        
        return motivo
