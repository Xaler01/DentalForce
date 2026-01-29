from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory
from datetime import datetime, timedelta, date
from .models import (
    Cita, Especialidad, Cubiculo, Paciente,
    DisponibilidadDentista, ExcepcionDisponibilidad,
    ComisionDentista, Clinica, Sucursal
)
from personal.models import Dentista
from django.contrib.auth.models import User


# Widget personalizado para Select Multiple que garantiza el atributo multiple
class Select2Multiple(forms.SelectMultiple):
    """Widget SelectMultiple con atributo multiple garantizado"""
    
    def __init__(self, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        # Forzar el atributo multiple
        attrs['multiple'] = 'multiple'
        super().__init__(attrs, choices)
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        # Asegurar que multiple esté presente
        attrs['multiple'] = 'multiple'
        return super().render(name, value, attrs, renderer)


# Widget personalizado para campos de fecha
class ISODateInput(forms.DateInput):
    """Widget personalizado que siempre renderiza fechas en formato ISO (YYYY-MM-DD)"""
    input_type = 'date'
    
    def __init__(self, attrs=None, format=None):
        # Siempre usar formato ISO, ignorar otros formatos
        super().__init__(attrs, format='%Y-%m-%d')
    
    def format_value(self, value):
        """Convertir fecha a formato ISO para HTML5"""
        if value is None or value == '':
            return ''
        if isinstance(value, str):
            # Si ya es string, intentar parsearlo y reformatearlo
            from datetime import datetime
            try:
                # Intentar parsear diferentes formatos
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        parsed = datetime.strptime(value, fmt)
                        return parsed.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                # Si no se pudo parsear, devolver tal cual
                return value
            except:
                return value
        # Si es un objeto date/datetime, convertir a ISO
        try:
            return value.strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            return str(value) if value else ''


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
        # Extraer clinica antes de super().__init__ si viene en kwargs
        self.clinica = kwargs.pop('clinica', None)
        super().__init__(*args, **kwargs)
        
        # Configurar formato de entrada para datetime-local
        self.fields['fecha_hora'].input_formats = ['%Y-%m-%dT%H:%M']

        # Filtrar catálogos para mostrar solo registros activos Y de la clínica activa
        if self.clinica:
            self.fields['paciente'].queryset = Paciente.objects.filter(
                estado=True, 
                clinica=self.clinica
            ).order_by('apellidos', 'nombres')
            self.fields['dentista'].queryset = Dentista.objects.filter(
                estado=True,
                sucursal_principal__clinica=self.clinica,
                sucursal_principal__estado=True  # Solo dentistas de sucursales activas
            ).select_related('usuario').order_by('usuario__last_name', 'usuario__first_name')
            # Filtrar cubículos: solo activos, de la clínica y de SUCURSALES ACTIVAS
            self.fields['cubiculo'].queryset = Cubiculo.objects.filter(
                estado=True,
                sucursal__estado=True,  # ⭐ CLAVE: Solo sucursales activas
                sucursal__clinica=self.clinica
            ).select_related('sucursal').order_by('sucursal__nombre', 'nombre')
        else:
            # Sin clínica, no mostrar nada (seguridad)
            self.fields['paciente'].queryset = Paciente.objects.none()
            self.fields['dentista'].queryset = Dentista.objects.none()
            self.fields['cubiculo'].queryset = Cubiculo.objects.none()
        
        # Si hay un dentista seleccionado, mostrar solo sus especialidades
        dentista = self.instance.dentista if self.instance.pk else None
        if dentista:
            self.fields['especialidad'].queryset = dentista.especialidades.filter(estado=True).order_by('nombre')
        else:
            # Si no hay dentista, mostrar todas las especialidades activas
            self.fields['especialidad'].queryset = Especialidad.objects.filter(estado=True).order_by('nombre')
        
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
                # No se permiten citas el mismo día - validar fecha y hora completas
                # Si la fecha es anterior a hoy, rechazar
                if fecha_hora.date() < ahora.date():
                    raise ValidationError('La fecha y hora de la cita no puede ser en el pasado')
                # Si es el mismo día, validar la hora
                elif fecha_hora.date() == ahora.date():
                    if fecha_hora < ahora:
                        raise ValidationError('La fecha y hora de la cita no puede ser en el pasado')
                # Si es una fecha futura, permitir
        
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
        # VALIDACIÓN 2.1: Sucursal del cubículo debe estar activa ⭐ NUEVO
        # ========================================================================
        if not cubiculo.sucursal.estado:
            raise ValidationError({
                'cubiculo': f'La sucursal "{cubiculo.sucursal.nombre}" está inactiva. '
                           f'No se pueden agendar citas en sucursales inactivas. '
                           f'Por favor, contacte al administrador.'
            })
        
        # ========================================================================
        # VALIDACIÓN 2.2: Cubículo debe estar activo ⭐ NUEVO
        # ========================================================================
        if not cubiculo.estado:
            raise ValidationError({
                'cubiculo': f'El cubículo "{cubiculo.nombre}" está inactivo. '
                           f'Por favor, seleccione otro cubículo disponible.'
            })
        
        # ========================================================================
        # VALIDACIÓN 2.3: Sucursal del dentista debe estar activa ⭐ NUEVO
        # ========================================================================
        if dentista.sucursal_principal and not dentista.sucursal_principal.estado:
            raise ValidationError({
                'dentista': f'La sucursal principal del dentista está inactiva. '
                           f'No se pueden agendar citas con este profesional.'
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

    def clean(self):
        """
        Evitar ejecutar la validación completa del modelo cuando solo se
        cancela la cita. Solo validar el motivo de cancelación aquí para
        que el formulario de cancelación no falle por validaciones de
        negocio que involucran campos que no se están editando.
        """
        cleaned_data = super(forms.ModelForm, self).clean()

        motivo = cleaned_data.get('motivo_cancelacion')
        if not motivo or len(motivo.strip()) < 10:
            raise ValidationError('Debe proporcionar un motivo de cancelación de al menos 10 caracteres')

        return cleaned_data


class CitaCancelSimpleForm(forms.Form):
    """
    Formulario sencillo para cancelar una cita que evita ejecutar
    validaciones de modelo complejas. Usado por la vista de
    cancelación para only validar el motivo de cancelación.
    """
    motivo_cancelacion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Por favor, indique el motivo de la cancelación...',
        }),
        label='Motivo de Cancelación',
        required=True,
        min_length=10,
    )

    def clean_motivo_cancelacion(self):
        motivo = self.cleaned_data.get('motivo_cancelacion', '')
        if not motivo or len(motivo.strip()) < 10:
            raise ValidationError('Debe proporcionar un motivo de cancelación de al menos 10 caracteres')
        return motivo


class EspecialidadForm(forms.ModelForm):
    """
    Formulario para crear y editar especialidades odontológicas.
    Incluye validaciones de negocio y widgets personalizados.
    """
    
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'duracion_default', 'color_calendario', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ortodoncia, Endodoncia, Periodoncia',
                'required': True,
                'maxlength': 100
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la especialidad (opcional)'
            }),
            'duracion_default': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'step': 15,
                'value': 30,
                'required': True
            }),
            'color_calendario': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'required': True
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Especialidad',
            'descripcion': 'Descripción',
            'duracion_default': 'Duración por Defecto (minutos)',
            'color_calendario': 'Color para Calendario',
            'estado': 'Activa'
        }
        help_texts = {
            'nombre': 'Nombre único de la especialidad',
            'descripcion': 'Descripción detallada de los servicios que incluye',
            'duracion_default': 'Duración estimada de una cita de esta especialidad',
            'color_calendario': 'Color que se mostrará en el calendario para esta especialidad',
            'estado': 'Solo las especialidades activas estarán disponibles para asignar'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar campos requeridos
        self.fields['nombre'].required = True
        self.fields['duracion_default'].required = True
        self.fields['color_calendario'].required = True
        
        # Valor por defecto para estado (solo en creación)
        if not self.instance.pk:
            self.fields['estado'].initial = True

    def clean_nombre(self):
        """
        Validación del nombre: único, sin espacios excesivos, capitalizado
        """
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre es obligatorio')
        
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres')
        
        # Verificar unicidad (excepto para la instancia actual en edición)
        if self.instance.pk:
            # Edición: excluir la instancia actual
            existe = Especialidad.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists()
        else:
            # Creación: verificar si existe
            existe = Especialidad.objects.filter(nombre__iexact=nombre).exists()
        
        if existe:
            raise ValidationError(f'Ya existe una especialidad con el nombre "{nombre}"')
        
        # Capitalizar primera letra de cada palabra
        nombre = nombre.title()
        
        return nombre

    def clean_duracion_default(self):
        """
        Validación de duración: debe ser múltiplo de 15 y entre 15-240 minutos
        """
        duracion = self.cleaned_data.get('duracion_default')
        
        if duracion < 15:
            raise ValidationError('La duración mínima es de 15 minutos')
        
        if duracion > 240:
            raise ValidationError('La duración máxima es de 4 horas (240 minutos)')
        
        if duracion % 15 != 0:
            raise ValidationError('La duración debe ser múltiplo de 15 minutos (15, 30, 45, 60...)')
        
        return duracion

    def clean_color_calendario(self):
        """
        Validación del color: formato hexadecimal válido
        """
        color = self.cleaned_data.get('color_calendario', '').strip()
        
        if not color:
            raise ValidationError('El color es obligatorio')
        
        # Validar formato hexadecimal
        if not color.startswith('#'):
            color = '#' + color
        
        if len(color) != 7:
            raise ValidationError('El color debe estar en formato hexadecimal (#RRGGBB)')
        
        return color.lower()


# ============================================================================
# FORMULARIO DE DENTISTA CON GESTIÓN DE HORARIOS
# ============================================================================

class DentistaForm(forms.ModelForm):
    """
    Formulario para crear y editar dentistas.
    Incluye campos relacionados con el usuario y validaciones de negocio.
    """
    
    # Campos adicionales para el usuario
    first_name = forms.CharField(
        max_length=150,
        label='Nombres',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombres del dentista'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos del dentista'
        })
    )
    username = forms.CharField(
        max_length=150,
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        }),
        help_text='Nombre de usuario para acceder al sistema'
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    password = forms.CharField(
        required=False,
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        }),
        help_text='Dejar en blanco para mantener la contraseña actual (solo en edición)'
    )
    
    class Meta:
        model = Dentista
        fields = [
            'especialidades',
            'sucursales',
            'sucursal_principal',
            'cedula_profesional',
            'numero_licencia',
            'telefono_movil',
            'fecha_contratacion',
            'biografia',
            'foto',
            'estado'
        ]
        widgets = {
            'especialidades': Select2Multiple(attrs={
                'class': 'form-control select2-especialidades',
                'data-placeholder': 'Seleccione una o más especialidades...',
                'required': True
            }),
            'sucursales': Select2Multiple(attrs={
                'class': 'form-control select2-sucursales',
                'data-placeholder': 'Seleccione las sucursales donde atiende...'
            }),
            'sucursal_principal': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'cedula_profesional': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234567890'
            }),
            'numero_licencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'LIC-12345'
            }),
            'telefono_movil': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0987654321',
                'type': 'tel'
            }),
            'fecha_contratacion': ISODateInput(attrs={
                'class': 'form-control'
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Experiencia profesional, estudios, especializaciones...'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'custom-control-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer clínica activa antes de super()
        self.clinica = kwargs.pop('clinica', None)
        
        # Si es edición, preparar valores iniciales antes de llamar super()
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].pk:
            instance = kwargs['instance']
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            # Establecer fecha_contratacion en initial
            if instance.fecha_contratacion:
                kwargs['initial']['fecha_contratacion'] = instance.fecha_contratacion
        
        super().__init__(*args, **kwargs)
        
        # Configurar múltiples formatos de fecha aceptados
        self.fields['fecha_contratacion'].input_formats = [
            '%Y-%m-%d',      # 2025-11-22 (ISO format)
            '%d/%m/%Y',      # 22/11/2025
            '%m/%d/%Y',      # 11/22/2025
        ]
        
        # FILTRAR ESPECIALIDADES: Solo mostrar las activas
        self.fields['especialidades'].queryset = Especialidad.objects.filter(
            estado=True
        ).order_by('nombre')
        
        # FILTRAR SUCURSALES: Solo mostrar las de la clínica activa
        if self.clinica:
            self.fields['sucursales'].queryset = Sucursal.objects.filter(
                estado=True,
                clinica=self.clinica
            ).order_by('nombre')
            self.fields['sucursal_principal'].queryset = Sucursal.objects.filter(
                estado=True,
                clinica=self.clinica
            ).order_by('nombre')
        else:
            # Sin clínica, no mostrar sucursales (seguridad)
            self.fields['sucursales'].queryset = Sucursal.objects.none()
            self.fields['sucursal_principal'].queryset = Sucursal.objects.none()
        
        # Si es edición, cargar datos del usuario
        if self.instance and self.instance.pk:
            usuario = self.instance.usuario
            self.fields['first_name'].initial = usuario.first_name
            self.fields['last_name'].initial = usuario.last_name
            self.fields['username'].initial = usuario.username
            self.fields['email'].initial = usuario.email
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Dejar en blanco para mantener la contraseña actual'
        else:
            # En creación, la contraseña es obligatoria
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Contraseña para acceder al sistema'
    
    def clean_username(self):
        """Validar que el username no exista (excepto en edición)"""
        username = self.cleaned_data.get('username', '').strip()
        
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio')
        
        # Si es edición, permitir el mismo username
        if self.instance and self.instance.pk:
            return username
        
        # Verificar si ya existe
        if User.objects.filter(username=username).exists():
            raise ValidationError(f'El nombre de usuario "{username}" ya está en uso')
        
        return username
    
    def clean_email(self):
        """Validar que el email no exista (excepto en edición)"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError('El email es obligatorio')
        
        # Si es edición, permitir el mismo email
        if self.instance and self.instance.pk:
            if self.instance.usuario.email != email:
                if User.objects.filter(email=email).exists():
                    raise ValidationError(f'El email "{email}" ya está en uso')
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError(f'El email "{email}" ya está en uso')
        
        return email
    
    def clean_cedula_profesional(self):
        """Validar formato y unicidad de cédula profesional"""
        cedula = self.cleaned_data.get('cedula_profesional', '').strip()
        
        if not cedula:
            raise ValidationError('La cédula profesional es obligatoria')
        
        # Validar formato (solo números y guiones)
        import re
        if not re.match(r'^[0-9\-]+$', cedula):
            raise ValidationError('La cédula solo puede contener números y guiones')
        
        # Verificar unicidad (excepto en edición)
        if self.instance and self.instance.pk:
            existe = Dentista.objects.filter(cedula_profesional=cedula).exclude(pk=self.instance.pk).exists()
        else:
            existe = Dentista.objects.filter(cedula_profesional=cedula).exists()
        
        if existe:
            raise ValidationError(f'Ya existe un dentista con la cédula "{cedula}"')
        
        return cedula
    
    def clean_numero_licencia(self):
        """Validar unicidad de número de licencia"""
        licencia = self.cleaned_data.get('numero_licencia', '').strip()
        
        if not licencia:
            raise ValidationError('El número de licencia es obligatorio')
        
        # Verificar unicidad (excepto en edición)
        if self.instance and self.instance.pk:
            existe = Dentista.objects.filter(numero_licencia=licencia).exclude(pk=self.instance.pk).exists()
        else:
            existe = Dentista.objects.filter(numero_licencia=licencia).exists()
        
        if existe:
            raise ValidationError(f'Ya existe un dentista con la licencia "{licencia}"')
        
        return licencia
    
    def clean_fecha_contratacion(self):
        """Validar que la fecha no sea futura"""
        fecha = self.cleaned_data.get('fecha_contratacion')
        
        if fecha and fecha > date.today():
            raise ValidationError('La fecha de contratación no puede ser futura')
        
        return fecha
    
    def clean_especialidades(self):
        """Validar que tenga al menos una especialidad"""
        especialidades = self.cleaned_data.get('especialidades')
        
        if not especialidades or especialidades.count() == 0:
            raise ValidationError('Debe seleccionar al menos una especialidad')
        
        return especialidades
    
    def save(self, commit=True, user=None):
        """Guardar dentista y crear/actualizar usuario"""
        dentista = super().save(commit=False)
        
        # Determinar si es creación o edición
        es_creacion = not self.instance.pk
        
        # Crear o actualizar usuario
        if es_creacion:
            # Creación: crear nuevo usuario
            usuario = User()
            usuario.username = self.cleaned_data['username']
        else:
            # Edición: actualizar usuario existente
            usuario = dentista.usuario
        
        usuario.first_name = self.cleaned_data['first_name']
        usuario.last_name = self.cleaned_data['last_name']
        usuario.email = self.cleaned_data['email']
        
        # Solo actualizar contraseña si se proporcionó
        password = self.cleaned_data.get('password')
        if password:
            usuario.set_password(password)
        
        if commit:
            # Guardar usuario primero
            usuario.save()
            
            # Asignar usuario al dentista
            dentista.usuario = usuario
            
            # Asignar uc (usuario creador) solo en creación
            if es_creacion and user:
                dentista.uc = user
            
            # Guardar dentista
            dentista.save()
            
            # Guardar relaciones M2M (especialidades)
            self.save_m2m()
        
        return dentista


class DisponibilidadDentistaForm(forms.ModelForm):
    """
    Formulario para gestionar la disponibilidad horaria de un dentista.
    """
    
    class Meta:
        model = DisponibilidadDentista
        fields = ['sucursal', 'dia_semana', 'hora_inicio', 'hora_fin', 'activo']
        widgets = {
            'sucursal': forms.Select(attrs={
                'class': 'form-control select2-sucursal-disponibilidad'
            }),
            'dia_semana': forms.Select(attrs={
                'class': 'form-control'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'sucursal': 'Sucursal',
            'dia_semana': 'Día',
            'hora_inicio': 'Hora Inicio',
            'hora_fin': 'Hora Fin',
            'activo': 'Activo'
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer el queryset de sucursales si se pasa
        sucursales_queryset = kwargs.pop('sucursales_queryset', None)
        
        super().__init__(*args, **kwargs)
        
        # Si se pasó un queryset específico, usarlo
        if sucursales_queryset is not None:
            self.fields['sucursal'].queryset = sucursales_queryset
        else:
            # Obtener el dentista desde la instancia
            dentista = None
            if hasattr(self.instance, 'dentista') and self.instance.dentista:
                dentista = self.instance.dentista
            
            # Configurar el queryset de sucursales
            if dentista:
                # Filtrar a las sucursales asignadas al dentista
                sucursales_disponibles = dentista.sucursales.all()
                if sucursales_disponibles.exists():
                    self.fields['sucursal'].queryset = sucursales_disponibles
                    # Si el dentista tiene sucursal principal, usarla como default para nuevos registros
                    if not self.instance.pk and dentista.sucursal_principal:
                        self.fields['sucursal'].initial = dentista.sucursal_principal
                else:
                    # Si no tiene sucursales asignadas, usar todas
                    from .models import Sucursal
                    self.fields['sucursal'].queryset = Sucursal.objects.filter(estado=True)
            else:
                # Si no hay dentista, mostrar todas las sucursales activas
                from .models import Sucursal
                self.fields['sucursal'].queryset = Sucursal.objects.filter(estado=True)
        
        # Hacer el campo opcional visualmente pero recomendado
        self.fields['sucursal'].required = False
        
        # Hacer hora_inicio y hora_fin opcionales en HTML (validación en clean())
        self.fields['hora_inicio'].required = False
        self.fields['hora_fin'].required = False
        
        # Establecer activo=False por defecto solo para nuevos registros
        if not self.instance.pk:
            self.fields['activo'].initial = False
    
    def clean(self):
        """Validaciones entre campos"""
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        activo = cleaned_data.get('activo', False)
        
        # Si está activo, debe tener horas definidas
        if activo:
            if not hora_inicio:
                raise ValidationError({
                    'hora_inicio': 'Debe especificar la hora de inicio para un horario activo'
                })
            if not hora_fin:
                raise ValidationError({
                    'hora_fin': 'Debe especificar la hora de fin para un horario activo'
                })
        
        # Validar que hora_fin sea posterior a hora_inicio (solo si ambas están presentes)
        if hora_inicio and hora_fin:
            if hora_inicio >= hora_fin:
                raise ValidationError({
                    'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio'
                })
        
        return cleaned_data


class ExcepcionDisponibilidadForm(forms.ModelForm):
    """
    Formulario para gestionar excepciones de disponibilidad (vacaciones, días libres, etc.)
    """
    
    class Meta:
        model = ExcepcionDisponibilidad
        fields = ['fecha_inicio', 'fecha_fin', 'tipo', 'motivo', 'todo_el_dia', 'hora_inicio', 'hora_fin', 'estado']
        widgets = {
            'fecha_inicio': ISODateInput(attrs={
                'class': 'form-control'
            }),
            'fecha_fin': ISODateInput(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Motivo de la excepción...'
            }),
            'todo_el_dia': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        # Si es edición y tenemos una instancia, preparar los valores iniciales
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].pk:
            instance = kwargs['instance']
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            if instance.fecha_inicio:
                kwargs['initial']['fecha_inicio'] = instance.fecha_inicio
            if instance.fecha_fin:
                kwargs['initial']['fecha_fin'] = instance.fecha_fin
        
        super().__init__(*args, **kwargs)
        
        # Configurar múltiples formatos de fecha aceptados
        self.fields['fecha_inicio'].input_formats = [
            '%Y-%m-%d',      # 2025-11-22 (ISO format)
            '%d/%m/%Y',      # 22/11/2025
            '%m/%d/%Y',      # 11/22/2025
        ]
        self.fields['fecha_fin'].input_formats = [
            '%Y-%m-%d',      # 2025-11-22 (ISO format)
            '%d/%m/%Y',      # 22/11/2025
            '%m/%d/%Y',      # 11/22/2025
        ]
        
        # Establecer estado=False por defecto solo para nuevos registros
        if not self.instance.pk:
            self.fields['estado'].initial = False
            self.fields['todo_el_dia'].initial = True
    
    def clean(self):
        """Validaciones entre campos - solo si estado está activo"""
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        
        # Solo validar si "Aplicar" está marcado
        if not estado:
            return cleaned_data
        
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        todo_el_dia = cleaned_data.get('todo_el_dia')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        # Validar que las fechas estén completas si está activo
        if not fecha_inicio:
            raise ValidationError({
                'fecha_inicio': 'Este campo es obligatorio cuando "Aplicar" está marcado'
            })
        
        if not fecha_fin:
            raise ValidationError({
                'fecha_fin': 'Este campo es obligatorio cuando "Aplicar" está marcado'
            })
        
        # Validar rango de fechas
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior o igual a la fecha de inicio'
                })
        
        # Si no es todo el día, validar horas
        if not todo_el_dia:
            if not hora_inicio or not hora_fin:
                raise ValidationError(
                    'Si no es todo el día, debe especificar hora de inicio y fin'
                )
            
            if hora_inicio >= hora_fin:
                raise ValidationError({
                    'hora_fin': 'La hora de fin debe ser posterior a la hora de inicio'
                })
        
        return cleaned_data



# Inline Formsets para Dentista
DisponibilidadDentistaFormSet = inlineformset_factory(
    Dentista,
    DisponibilidadDentista,
    form=DisponibilidadDentistaForm,
    extra=7,  # 7 días de la semana
    max_num=14,  # Permitir hasta 2 horarios por día
    can_delete=True
)


class ComisionDentistaForm(forms.ModelForm):
    """
    Formulario para gestionar comisiones de dentistas por especialidad.
    Permite configurar comisiones por porcentaje o valor fijo.
    Solo muestra especialidades activas o asignadas al dentista.
    """
    
    class Meta:
        model = ComisionDentista
        fields = ['especialidad', 'tipo_comision', 'porcentaje', 'valor_fijo', 'activo', 'observaciones']
        widgets = {
            'especialidad': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'tipo_comision': forms.Select(attrs={
                'class': 'form-control tipo-comision-select'
            }),
            'porcentaje': forms.NumberInput(attrs={
                'class': 'form-control campo-porcentaje',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Ej: 15.50'
            }),
            'valor_fijo': forms.NumberInput(attrs={
                'class': 'form-control campo-valor-fijo',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Ej: 50.00'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales sobre esta comisión...'
            })
        }
        labels = {
            'especialidad': 'Especialidad',
            'tipo_comision': 'Tipo de Comisión',
            'porcentaje': 'Porcentaje (%)',
            'valor_fijo': 'Valor Fijo ($)',
            'activo': 'Activo',
            'observaciones': 'Observaciones'
        }
        help_texts = {
            'especialidad': 'Seleccione la especialidad para esta comisión',
            'tipo_comision': 'Porcentaje del tratamiento o valor fijo por atención',
            'porcentaje': 'Porcentaje de comisión (0-100%)',
            'valor_fijo': 'Monto fijo en dólares por tratamiento',
            'activo': 'Marque para activar esta comisión',
            'observaciones': 'Información adicional (opcional)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar especialidades: solo mostrar especialidades activas
        from clinicas.models import Especialidad
        self.fields['especialidad'].queryset = Especialidad.objects.filter(
            estado=True
        ).order_by('nombre')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['activo'].initial = False
            if 'porcentaje' not in self.initial:
                self.fields['porcentaje'].initial = 20
            if 'tipo_comision' not in self.initial:
                self.fields['tipo_comision'].initial = 'PORCENTAJE'
    
    def clean(self):
        """Validaciones personalizadas del formulario"""
        cleaned_data = super().clean()
        tipo_comision = cleaned_data.get('tipo_comision')
        porcentaje = cleaned_data.get('porcentaje')
        valor_fijo = cleaned_data.get('valor_fijo')
        especialidad = cleaned_data.get('especialidad')
        activo = cleaned_data.get('activo', False)
        
        # Solo validar si la comisión está activa
        if not activo:
            return cleaned_data
        
        # Si está activa, validar que tenga especialidad
        if not especialidad:
            raise ValidationError({
                'especialidad': 'Debe seleccionar una especialidad para activar la comisión'
            })
        
        if not tipo_comision:
            raise ValidationError({
                'tipo_comision': 'Debe seleccionar un tipo de comisión'
            })
        
        # Validar según el tipo de comisión seleccionado
        if tipo_comision == 'PORCENTAJE':
            if not porcentaje or porcentaje <= 0:
                raise ValidationError({
                    'porcentaje': 'Debe especificar un porcentaje mayor a 0 cuando selecciona "Porcentaje"'
                })
            cleaned_data['valor_fijo'] = None
        
        elif tipo_comision == 'FIJO':
            if not valor_fijo or valor_fijo <= 0:
                raise ValidationError({
                    'valor_fijo': 'Debe especificar un valor mayor a 0 cuando selecciona "Valor Fijo"'
                })
            cleaned_data['porcentaje'] = None
        
        return cleaned_data


ExcepcionDisponibilidadFormSet = inlineformset_factory(
    Dentista,
    ExcepcionDisponibilidad,
    form=ExcepcionDisponibilidadForm,
    extra=1,
    can_delete=False
)


ComisionDentistaFormSet = inlineformset_factory(
    Dentista,
    ComisionDentista,
    form=ComisionDentistaForm,
    extra=1,
    can_delete=True
)

class CubiculoForm(forms.ModelForm):
    class Meta:
        model = Cubiculo
        fields = ['nombre', 'numero', 'capacidad', 'descripcion', 'equipamiento', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Consultorio 1'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Uso, ubicación, notas'}),
            'equipamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Sillón, RX, etc.'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre',
            'numero': 'Número',
            'capacidad': 'Capacidad',
            'descripcion': 'Descripción',
            'equipamiento': 'Equipamiento',
            'estado': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['estado'].initial = True


CubiculoFormSet = inlineformset_factory(
    Sucursal,
    Cubiculo,
    form=CubiculoForm,
    extra=1,
    can_delete=True
)

ExcepcionDisponibilidadFormSet = inlineformset_factory(
    Dentista,
    ExcepcionDisponibilidad,
    form=ExcepcionDisponibilidadForm,
    extra=1,  # Solo mostrar 1 fila vacía, se pueden agregar más con JavaScript
    can_delete=False  # No eliminar físicamente, desactivar con estado=False para mantener histórico
)


class ClinicaForm(forms.ModelForm):
    """Formulario para crear y editar clínicas con datos fiscales e internacionales"""
    
    class Meta:
        model = Clinica
        fields = [
            'nombre', 'eslogan', 'titulo_pestana', 'direccion', 'telefono', 'email',
            'ruc', 'razon_social', 'representante_legal',
            'pais', 'moneda', 'zona_horaria',
            'logo', 'sitio_web'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre comercial de la clínica',
                'maxlength': '150'
            }),
            'eslogan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: "Cuidamos tu sonrisa" (opcional)',
                'maxlength': '80'
            }),
            'titulo_pestana': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: "Clínica Tío Alex | Tu salud oral primero" (opcional)',
                'maxlength': '180'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa',
                'rows': 2
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '02-XXXXXXX o 09XXXXXXXX',
                'maxlength': '20'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@clinica.com',
                'maxlength': '100'
            }),
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUC/NIT/CUIT según país',
                'maxlength': '20'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón social para facturas (opcional)',
                'maxlength': '200'
            }),
            'representante_legal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del representante legal (opcional)',
                'maxlength': '150'
            }),
            'pais': forms.Select(attrs={
                'class': 'form-control'
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-control'
            }),
            'zona_horaria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'America/Guayaquil',
                'maxlength': '50'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'sitio_web': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.clinica.com (opcional)'
            }),
        }
        labels = {
            'nombre': 'Nombre Comercial',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Email',
            'ruc': 'RUC/NIT/CUIT',
            'razon_social': 'Razón Social',
            'representante_legal': 'Representante Legal',
            'pais': 'País',
            'moneda': 'Moneda',
            'zona_horaria': 'Zona Horaria',
            'logo': 'Logo',
            'sitio_web': 'Sitio Web',
        }
        help_texts = {
            'ruc': 'Ecuador: 13 dígitos, Perú: 11 dígitos, Colombia: 9-10 dígitos',
            'razon_social': 'Nombre legal de la empresa (si es diferente al nombre comercial)',
            'zona_horaria': 'Zona horaria del país donde opera la clínica',
        }
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email:
            # Verificar si ya existe otra clínica con este email
            qs = Clinica.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Ya existe una clínica con este email.')
        return email
    
    def clean_telefono(self):
        """Validar formato de teléfono"""
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Remover espacios y guiones
            telefono_limpio = telefono.replace(' ', '').replace('-', '')
            # Validar longitud
            if len(telefono_limpio) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        return telefono
    
    def clean(self):
        """Validaciones cruzadas"""
        import re
        cleaned_data = super().clean()
        pais = cleaned_data.get('pais')
        moneda = cleaned_data.get('moneda')
        ruc = cleaned_data.get('ruc')
        
        # Validar RUC según país
        if ruc and pais:
            ruc_limpio = re.sub(r'[^0-9A-Z]', '', ruc.upper())
            
            if pais == 'EC':  # Ecuador: 13 dígitos
                if not re.match(r'^\d{13}$', ruc_limpio):
                    self.add_error('ruc', 'El RUC de Ecuador debe tener 13 dígitos numéricos.')
            elif pais == 'PE':  # Perú: 11 dígitos
                if not re.match(r'^\d{11}$', ruc_limpio):
                    self.add_error('ruc', 'El RUC de Perú debe tener 11 dígitos numéricos.')
            elif pais == 'CO':  # Colombia: 9-10 dígitos
                if not re.match(r'^\d{9,10}$', ruc_limpio):
                    self.add_error('ruc', 'El NIT de Colombia debe tener entre 9 y 10 dígitos.')
            elif pais == 'MX':  # México: RFC 12-13 caracteres alfanuméricos
                if not re.match(r'^[A-Z0-9]{12,13}$', ruc_limpio):
                    self.add_error('ruc', 'El RFC de México debe tener entre 12 y 13 caracteres alfanuméricos.')
        
        # Sugerir moneda correcta según país
        monedas_por_pais = {
            'EC': 'USD',
            'PE': 'PEN',
            'CO': 'COP',
            'MX': 'MXN',
            'CL': 'CLP',
            'AR': 'ARS',
        }
        
        if pais and moneda:
            moneda_sugerida = monedas_por_pais.get(pais)
            if moneda != moneda_sugerida:
                self.add_error('moneda', 
                    f'La moneda sugerida para {dict(Clinica.PAISES_CHOICES).get(pais)} es {moneda_sugerida}')
        
        return cleaned_data


# ============================================================================
# FORMULARIO DE SUCURSALES
# ============================================================================

class SucursalForm(forms.ModelForm):
    """Formulario para crear y editar sucursales"""
    
    # Choices para días de la semana
    DIAS_CHOICES = [
        ('L', 'Lunes'),
        ('M', 'Martes'),
        ('X', 'Miércoles'),
        ('J', 'Jueves'),
        ('V', 'Viernes'),
        ('S', 'Sábado'),
        ('D', 'Domingo'),
    ]
    
    # Campo personalizado para días de atención con checkboxes
    dias_atencion_checkboxes = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=True,
        label='Días de Atención',
        help_text='Selecciona los días en que la sucursal atiende'
    )
    
    class Meta:
        model = Sucursal
        fields = [
            'clinica',
            'nombre',
            'direccion',
            'telefono',
            'horario_apertura',
            'horario_cierre',
            'sabado_horario_apertura',
            'sabado_horario_cierre',
            'domingo_horario_apertura',
            'domingo_horario_cierre',
        ]
        widgets = {
            'clinica': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sucursal Centro, Sucursal Norte',
                'maxlength': '150',
                'required': True
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa de la sucursal',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 0999-123456',
                'maxlength': '20',
                'required': True
            }),
            'horario_apertura': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 08:00)',
                'required': True,
                'autocomplete': 'off'
            }),
            'horario_cierre': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 18:00)',
                'required': True,
                'autocomplete': 'off'
            }),
            'sabado_horario_apertura': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 08:00)',
                'autocomplete': 'off'
            }),
            'sabado_horario_cierre': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 13:00)',
                'autocomplete': 'off'
            }),
            'domingo_horario_apertura': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 09:00)',
                'autocomplete': 'off'
            }),
            'domingo_horario_cierre': forms.TextInput(attrs={
                'class': 'form-control datetimepicker-time',
                'placeholder': 'HH:MM (ej: 13:00)',
                'autocomplete': 'off'
            }),
        }
        labels = {
            'clinica': 'Clínica',
            'nombre': 'Nombre de la Sucursal',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'horario_apertura': 'Hora de Apertura (L-V)',
            'horario_cierre': 'Hora de Cierre (L-V)',
            'sabado_horario_apertura': 'Apertura Sábado',
            'sabado_horario_cierre': 'Cierre Sábado',
            'domingo_horario_apertura': 'Apertura Domingo',
            'domingo_horario_cierre': 'Cierre Domingo',
        }
        help_texts = {
            'clinica': 'Selecciona la clínica a la que pertenece esta sucursal',
            'nombre': 'Nombre identificador de la sucursal (debe ser único por clínica)',
            'direccion': 'Dirección completa donde se ubica la sucursal',
            'telefono': 'Número de teléfono de contacto de la sucursal',
            'horario_apertura': 'Hora en que abre la sucursal de Lunes a Viernes',
            'horario_cierre': 'Hora en que cierra la sucursal de Lunes a Viernes',
            'sabado_horario_apertura': 'Dejar vacío para usar horario L-V',
            'sabado_horario_cierre': 'Dejar vacío para usar horario L-V',
            'domingo_horario_apertura': 'Dejar vacío para usar horario L-V',
            'domingo_horario_cierre': 'Dejar vacío para usar horario L-V',
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer el usuario del kwargs si viene
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Guardar el usuario para usarlo en clean_clinica
        self._user = user
        
        # Si estamos editando, cargar los días seleccionados
        if self.instance and self.instance.pk and self.instance.dias_atencion:
            # Convertir string "LMXJV" a lista ['L', 'M', 'X', 'J', 'V']
            dias_list = list(self.instance.dias_atencion)
            self.initial['dias_atencion_checkboxes'] = dias_list
        
        # Filtrar clínicas según el usuario
        if user:
            if not user.is_superuser:
                # Para admins de clínica: mostrar solo su clínica, hacerla readonly
                try:
                    from usuarios.models import UsuarioClinica
                    usuario_clinica = UsuarioClinica.objects.filter(usuario=user).first()
                    if usuario_clinica and usuario_clinica.clinica:
                        clinica = usuario_clinica.clinica
                        # Filtrar queryset a solo la clínica del usuario
                        self.fields['clinica'].queryset = Clinica.objects.filter(pk=clinica.pk)
                        # Pre-seleccionar la clínica del usuario
                        self.initial['clinica'] = clinica
                        # Deshabilitar el campo
                        self.fields['clinica'].disabled = True
                        self.fields['clinica'].widget.attrs.update({
                            'disabled': 'disabled',
                            'style': 'background-color: #e9ecef; cursor: not-allowed; pointer-events: none;'
                        })
                        self.fields['clinica'].help_text = f'Asignado a: {clinica.nombre}'
                    else:
                        # Si no tiene clínica asignada, mostrar todas
                        self.fields['clinica'].queryset = Clinica.objects.filter(estado=True).order_by('nombre')
                except Exception as e:
                    # Si hay error, usar comportamiento por defecto
                    self.fields['clinica'].queryset = Clinica.objects.filter(estado=True).order_by('nombre')
            else:
                # Para superusers: mostrar todas las clínicas activas
                self.fields['clinica'].queryset = Clinica.objects.filter(estado=True).order_by('nombre')
        else:
            # Si no viene user, mostrar todas (fallback)
            self.fields['clinica'].queryset = Clinica.objects.filter(estado=True).order_by('nombre')
    
    def clean_clinica(self):
        """
        Validación backend: asegurar que admins de clínica solo puedan 
        asignar su propia clínica
        """
        clinica = self.cleaned_data.get('clinica')
        
        # Obtener el usuario desde el formulario (guardado en __init__)
        if hasattr(self, '_user') and self._user and not self._user.is_superuser:
            from usuarios.models import UsuarioClinica
            usuario_clinica = UsuarioClinica.objects.filter(usuario=self._user).first()
            if usuario_clinica and usuario_clinica.clinica:
                # Forzar que sea la clínica del usuario, ignorando lo que venga del POST
                return usuario_clinica.clinica
        
        return clinica
    
    def clean_nombre(self):
        """Validar que el nombre no esté vacío y sea único por clínica"""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre de la sucursal es requerido.')
        
        # Validar unicidad por clínica (solo en creación o si cambió el nombre)
        clinica = self.cleaned_data.get('clinica')
        if clinica:
            qs = Sucursal.objects.filter(clinica=clinica, nombre__iexact=nombre)
            
            # Si estamos editando, excluir la instancia actual
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Ya existe una sucursal con el nombre "{nombre}" para la clínica {clinica.nombre}'
                )
        
        return nombre
    
    def clean_telefono(self):
        """Validar formato de teléfono"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if not telefono:
            raise ValidationError('El teléfono es requerido.')
        
        # Remover espacios, guiones y paréntesis para validar
        telefono_limpio = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        if len(telefono_limpio) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        
        return telefono
    
    def clean(self):
        """Validaciones cruzadas"""
        cleaned_data = super().clean()
        
        horario_apertura = cleaned_data.get('horario_apertura')
        horario_cierre = cleaned_data.get('horario_cierre')
        dias_checkboxes = cleaned_data.get('dias_atencion_checkboxes')
        
        # Validar que el horario de cierre sea posterior al de apertura
        if horario_apertura and horario_cierre:
            if horario_cierre <= horario_apertura:
                self.add_error('horario_cierre', 
                    'La hora de cierre debe ser posterior a la hora de apertura.')
        
        # Validar que se haya seleccionado al menos un día
        if not dias_checkboxes:
            self.add_error('dias_atencion_checkboxes', 
                'Debe seleccionar al menos un día de atención.')
        
        # Convertir lista de días a string "LMXJV" para guardar en el modelo
        if dias_checkboxes:
            # Ordenar según el orden de la semana
            orden_dias = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
            dias_ordenados = [dia for dia in orden_dias if dia in dias_checkboxes]
            cleaned_data['dias_atencion'] = ''.join(dias_ordenados)
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar con el campo dias_atencion procesado"""
        instance = super().save(commit=False)
        
        # El campo dias_atencion ya está en cleaned_data por el método clean()
        if 'dias_atencion' in self.cleaned_data:
            instance.dias_atencion = self.cleaned_data['dias_atencion']
        
        if commit:
            instance.save()
        
        return instance

