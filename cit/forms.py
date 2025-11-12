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
        fecha_hora = self.cleaned_data.get('fecha_hora')
        
        if not fecha_hora:
            raise ValidationError('Debe seleccionar una fecha y hora para la cita')
        
        # Validar que la fecha no sea en el pasado (solo para nuevas citas o si cambió la fecha)
        ahora = timezone.now()
        
        # Para ediciones, permitir si la fecha no cambió
        if self.instance.pk:
            if self.instance.fecha_hora == fecha_hora:
                return fecha_hora
        
        # Para nuevas citas o cambios de fecha, validar que sea futura
        if fecha_hora < ahora:
            raise ValidationError('La fecha y hora de la cita no puede ser en el pasado')
        
        # Validar que no sea más de 6 meses en el futuro
        seis_meses = ahora + timedelta(days=180)
        if fecha_hora > seis_meses:
            raise ValidationError('La cita no puede ser programada con más de 6 meses de anticipación')
        
        # Validar horario de atención (de 8:00 AM a 8:00 PM)
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
        
        # Solo validar si todos los campos necesarios están presentes
        if not all([dentista, especialidad, cubiculo, fecha_hora, duracion]):
            return cleaned_data
        
        # Validar que el dentista tenga la especialidad
        if especialidad not in dentista.especialidades.all():
            raise ValidationError({
                'especialidad': f'El Dr./Dra. {dentista} no tiene certificación en {especialidad}'
            })
        
        # Validar que el cubículo pertenezca a la sucursal del dentista
        if dentista.sucursal_principal and cubiculo.sucursal != dentista.sucursal_principal:
            raise ValidationError({
                'cubiculo': f'El cubículo debe pertenecer a la sucursal {dentista.sucursal_principal}'
            })
        
        # Validar disponibilidad del dentista
        fecha_fin = fecha_hora + timedelta(minutes=duracion)
        
        # Excluir la cita actual si es edición
        citas_dentista = Cita.objects.filter(
            dentista=dentista,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=self.instance.pk if self.instance.pk else None)
        
        for cita in citas_dentista:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                raise ValidationError({
                    'fecha_hora': f'El Dr./Dra. {dentista} ya tiene una cita programada en este horario '
                                  f'({cita.fecha_hora.strftime("%d/%m/%Y %H:%M")})'
                })
        
        # Validar disponibilidad del cubículo
        citas_cubiculo = Cita.objects.filter(
            cubiculo=cubiculo,
            fecha_hora__lt=fecha_fin,
            estado__in=[Cita.ESTADO_PENDIENTE, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_ATENCION]
        ).exclude(pk=self.instance.pk if self.instance.pk else None)
        
        for cita in citas_cubiculo:
            cita_fin = cita.fecha_hora + timedelta(minutes=cita.duracion)
            if cita.fecha_hora < fecha_fin and cita_fin > fecha_hora:
                raise ValidationError({
                    'cubiculo': f'El cubículo {cubiculo} ya está ocupado en este horario '
                                f'({cita.fecha_hora.strftime("%d/%m/%Y %H:%M")})'
                })
        
        # Validar citas en domingo requieren confirmación
        if fecha_hora.weekday() == 6:  # 6 = domingo
            estado = cleaned_data.get('estado', Cita.ESTADO_PENDIENTE)
            if estado == Cita.ESTADO_PENDIENTE and not self.instance.pk:
                raise ValidationError({
                    'estado': 'Las citas programadas para domingo deben estar confirmadas desde su creación'
                })
        
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
