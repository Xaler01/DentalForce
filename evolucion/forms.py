"""
Formularios para evolución odontológica.
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone
from evolucion.models import (
    EvolucionConsulta,
    ProcedimientoEnEvolucion,
    PlanTratamiento,
    ProcedimientoEnPlan,
    HistoriaClinicaOdontologica,
)


class EvolucionConsultaForm(forms.ModelForm):
    """
    Formulario para crear/editar evoluciones de consulta.
    """
    
    class Meta:
        model = EvolucionConsulta
        fields = [
            'fecha_consulta',
            'cita',
            'motivo_consulta',
            'hallazgos_clinicos',
            'recomendaciones',
            'cambios_odontograma',
            'fecha_proximo_control',
        ]
        widgets = {
            'fecha_consulta': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True,
                }
            ),
            'cita': forms.Select(
                attrs={
                    'class': 'form-control select2',
                }
            ),
            'motivo_consulta': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe la queja principal del paciente',
                    'required': True,
                }
            ),
            'hallazgos_clinicos': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Hallazgos clínicos encontrados durante la consulta',
                }
            ),
            'recomendaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Recomendaciones para el paciente (higiene, medicinas, etc.)',
                }
            ),
            'cambios_odontograma': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Cambios realizados en el odontograma',
                }
            ),
            'fecha_proximo_control': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
        }
    
    def __init__(self, *args, paciente=None, clinica=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.paciente = paciente
        self.clinica = clinica
        
        # Si el paciente existe, filtrar citas del paciente
        if paciente:
            from cit.models import Cita
            self.fields['cita'].queryset = Cita.objects.filter(
                paciente=paciente
            ).select_related('paciente__clinica', 'dentista', 'especialidad', 'cubiculo')
            # Hacer cita opcional
            self.fields['cita'].required = False
    
    def clean_fecha_consulta(self):
        """Valida que la fecha no sea en el futuro."""
        fecha = self.data.get('fecha_consulta')
        if fecha:
            fecha_obj = timezone.datetime.strptime(fecha, '%Y-%m-%d').date()
            if fecha_obj > timezone.now().date():
                raise ValidationError("La fecha de consulta no puede ser en el futuro.")
        return self.cleaned_data.get('fecha_consulta')
    
    def clean_motivo_consulta(self):
        """Valida que el motivo de consulta no esté vacío."""
        motivo = self.cleaned_data.get('motivo_consulta', '').strip()
        if not motivo:
            raise ValidationError("El motivo de consulta es obligatorio.")
        return motivo
    
    def clean_fecha_proximo_control(self):
        """Valida que la próxima cita sea en el futuro."""
        fecha_consulta = self.data.get('fecha_consulta')
        fecha_proximo = self.cleaned_data.get('fecha_proximo_control')
        
        if fecha_proximo and fecha_consulta:
            fecha_consulta_obj = timezone.datetime.strptime(fecha_consulta, '%Y-%m-%d').date()
            if fecha_proximo <= fecha_consulta_obj:
                raise ValidationError(
                    "La próxima cita debe ser después de la fecha de consulta actual."
                )
        return fecha_proximo


class ProcedimientoEnEvolucionForm(forms.ModelForm):
    """
    Formulario para agregar procedimientos a una evolución.
    """
    
    class Meta:
        model = ProcedimientoEnEvolucion
        fields = ['procedimiento', 'cantidad', 'observaciones']
        widgets = {
            'procedimiento': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'required': True,
                }
            ),
            'cantidad': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'value': '1',
                    'type': 'number',
                }
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Observaciones específicas del procedimiento (opcional)',
                }
            ),
        }
    
    def clean_cantidad(self):
        """Valida que la cantidad sea positiva."""
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad < 1:
            raise ValidationError("La cantidad debe ser mayor a 0.")
        return cantidad


class PlanTratamientoForm(forms.ModelForm):
    """
    Formulario para crear/editar planes de tratamiento.
    """
    
    class Meta:
        model = PlanTratamiento
        fields = [
            'nombre',
            'descripcion',
            'estado',
            'prioridad',
            'fecha_inicio',
            'fecha_estimada_fin',
            'presupuesto_estimado',
        ]
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del plan de tratamiento',
                    'required': True,
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Descripción detallada del plan',
                }
            ),
            'estado': forms.Select(
                attrs={
                    'class': 'form-control',
                }
            ),
            'prioridad': forms.Select(
                attrs={
                    'class': 'form-control',
                }
            ),
            'fecha_inicio': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'fecha_estimada_fin': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'presupuesto_estimado': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                    'type': 'number',
                    'placeholder': '0.00',
                    'required': True,
                }
            ),
        }
    
    def clean_nombre(self):
        """Valida que el nombre no esté vacío."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError("El nombre del plan es obligatorio.")
        return nombre
    
    def clean_presupuesto_estimado(self):
        """Valida que el presupuesto sea positivo."""
        presupuesto = self.cleaned_data.get('presupuesto_estimado')
        if presupuesto and presupuesto < 0:
            raise ValidationError("El presupuesto no puede ser negativo.")
        return presupuesto
    
    def clean(self):
        """Valida coherencia entre fechas."""
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_estimada_fin = cleaned_data.get('fecha_estimada_fin')
        
        if fecha_inicio and fecha_estimada_fin:
            if fecha_estimada_fin <= fecha_inicio:
                raise ValidationError(
                    "La fecha estimada de fin debe ser posterior a la fecha de inicio."
                )
        
        return cleaned_data


class ProcedimientoEnPlanForm(forms.ModelForm):
    """
    Formulario para agregar procedimientos a un plan.
    """
    
    class Meta:
        model = ProcedimientoEnPlan
        fields = ['procedimiento', 'orden', 'precio', 'observaciones']
        widgets = {
            'procedimiento': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'required': True,
                }
            ),
            'orden': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'type': 'number',
                    'value': '0',
                }
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                    'type': 'number',
                    'placeholder': '0.00',
                    'required': True,
                }
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Observaciones (opcional)',
                }
            ),
        }
    
    def clean_precio(self):
        """Valida que el precio sea positivo."""
        precio = self.cleaned_data.get('precio')
        if precio and precio < 0:
            raise ValidationError("El precio no puede ser negativo.")
        return precio


class BuscarEvolucionForm(forms.Form):
    """
    Formulario para buscar evoluciones.
    """
    
    paciente = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Paciente',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2',
                'placeholder': 'Selecciona un paciente',
            }
        )
    )
    
    fecha_desde = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        )
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        )
    )
    
    dentista = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Dentista',
        widget=forms.Select(
            attrs={
                'class': 'form-control select2',
                'placeholder': 'Selecciona un dentista',
            }
        )
    )
    
    def __init__(self, *args, clinica=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        from pacientes.models import Paciente
        from personal.models import Dentista
        
        if clinica:
            # Filtrar pacientes por clínica
            self.fields['paciente'].queryset = Paciente.objects.filter(
                clinica=clinica
            ).order_by('nombres')
            
            # Filtrar dentistas por clínica (a través de sucursal)
            self.fields['dentista'].queryset = Dentista.objects.filter(
                sucursal_principal__clinica=clinica
            ).order_by('usuario__first_name')
        else:
            self.fields['paciente'].queryset = Paciente.objects.all().order_by('nombres')
            self.fields['dentista'].queryset = Dentista.objects.all().order_by('usuario__first_name')
    
    def clean(self):
        """Valida que fecha_desde sea anterior a fecha_hasta."""
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError("La fecha desde debe ser anterior a la fecha hasta.")
        
        return cleaned_data


class HistoriaClinicaOdontologicaForm(forms.ModelForm):
    """
    Formulario para crear/editar historia clínica odontológica.
    """
    
    class Meta:
        model = HistoriaClinicaOdontologica
        fields = [
            'antecedentes_medicos',
            'antecedentes_odontologicos',
            'alergias',
            'medicamentos_actuales',
            'fuma',
            'consume_alcohol',
            'bruxismo',
            'frecuencia_cepillado',
            'usa_seda_dental',
            'estado_encias',
            'presencia_sarro',
            'presencia_caries',
            'observaciones_clinicas',
        ]
        widgets = {
            'antecedentes_medicos': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Enfermedades sistémicas, cirugías previas, etc.',
                }
            ),
            'antecedentes_odontologicos': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Procedimientos dentales previos, problemas anteriores, etc.',
                }
            ),
            'alergias': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Alergias a medicamentos, materiales, etc.',
                }
            ),
            'medicamentos_actuales': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Medicamentos que está tomando actualmente',
                }
            ),
            'fuma': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'consume_alcohol': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'bruxismo': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'frecuencia_cepillado': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 2-3 veces al día',
                }
            ),
            'usa_seda_dental': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'estado_encias': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Observaciones sobre el estado de las encías',
                }
            ),
            'presencia_sarro': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'presencia_caries': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
            'observaciones_clinicas': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Otras observaciones clínicas relevantes',
                }
            ),
        }


# Formsets for inline editing
ProcedimientoEnEvolucionFormSet = inlineformset_factory(
    EvolucionConsulta,
    ProcedimientoEnEvolucion,
    form=ProcedimientoEnEvolucionForm,
    extra=1,
    can_delete=True,
)

ProcedimientoEnPlanFormSet = inlineformset_factory(
    PlanTratamiento,
    ProcedimientoEnPlan,
    form=ProcedimientoEnPlanForm,
    extra=1,
    can_delete=True,
)
