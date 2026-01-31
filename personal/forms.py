from django import forms
from django.contrib.auth.models import User

from core.services.tenants import get_clinica_from_request
from .models import Personal, RegistroHorasPersonal, ExcepcionPersonal


class PersonalForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		request = kwargs.pop('request', None)
		super().__init__(*args, **kwargs)

		if request:
			clinica_activa = get_clinica_from_request(request)
			if clinica_activa and not request.user.is_superuser:
				self.fields['sucursal_principal'].queryset = self.fields['sucursal_principal'].queryset.filter(
					clinica=clinica_activa,
					estado=True,
				)
				self.fields['sucursales'].queryset = self.fields['sucursales'].queryset.filter(
					clinica=clinica_activa,
					estado=True,
				)
				self.fields['usuario'].queryset = User.objects.filter(
					clinica_asignacion__clinica=clinica_activa,
					clinica_asignacion__activo=True,
				).order_by('first_name', 'last_name', 'username')
	class Meta:
		model = Personal
		fields = [
			'usuario',
			'tipo_personal',
			'sucursal_principal',
			'sucursales',
			'tipo_compensacion',
			'salario_mensual',
			'tarifa_por_hora',
			'tarifa_por_dia',
			'fecha_contratacion',
			'estado'
		]
		widgets = {
			'usuario': forms.Select(attrs={'class': 'form-control'}),
			'tipo_personal': forms.Select(attrs={'class': 'form-control'}),
			'sucursal_principal': forms.Select(attrs={'class': 'form-control'}),
			'sucursales': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
			'tipo_compensacion': forms.Select(attrs={'class': 'form-control'}),
			'salario_mensual': forms.NumberInput(attrs={'class': 'form-control'}),
			'tarifa_por_hora': forms.NumberInput(attrs={'class': 'form-control'}),
			'tarifa_por_dia': forms.NumberInput(attrs={'class': 'form-control'}),
			'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
		}


class RegistroHorasPersonalForm(forms.ModelForm):
	monto_pago_dia = forms.DecimalField(
		required=False,
		max_digits=6,
		decimal_places=2,
		widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '20.00'}),
		label='Monto por Día (opcional)',
		help_text='Solo para trabajo por día (ej: limpieza). Dejar vacío para horas extra normales'
	)
	
	class Meta:
		model = RegistroHorasPersonal
		fields = ['fecha', 'hora_inicio', 'hora_fin', 'observaciones']
		widgets = {
			'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
			'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
			'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
			'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observaciones opcionales'}),
		}
		labels = {
			'hora_inicio': 'Hora Inicio',
			'hora_fin': 'Hora Fin',
			'observaciones': 'Observaciones',
			'fecha': 'Fecha',
		}
		help_texts = {
			'hora_inicio': 'Hora en que iniciaron las horas extra',
			'hora_fin': 'Hora en que terminaron las horas extra. Si cruza las 20:00, se desglosará automáticamente',
		}

	def __init__(self, *args, **kwargs):
		request = kwargs.pop('request', None)
		super().__init__(*args, **kwargs)
		# Configurar formatos de entrada para compatibilidad con HTML5
		self.fields['fecha'].input_formats = ['%Y-%m-%d']
		self.fields['hora_inicio'].input_formats = ['%H:%M']
		self.fields['hora_fin'].input_formats = ['%H:%M']
		
		# Asignar personal al instance si está disponible
		if request and hasattr(request.user, 'personal_profile'):
			self.instance.personal = request.user.personal_profile

	def clean(self):
		cleaned_data = super().clean()
		hora_inicio = cleaned_data.get('hora_inicio')
		hora_fin = cleaned_data.get('hora_fin')
		fecha = cleaned_data.get('fecha')

		if hora_inicio and hora_fin:
			if hora_inicio >= hora_fin:
				raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
		
		# Validar que no haya conflictos de horarios si es para crear (no actualizar)
		if fecha and hora_inicio and hora_fin and not self.instance.pk:
			# Obtener el personal del usuario actual (se asignará en la vista)
			# Por ahora, simplemente validar que el modelo lo haga en save()
			pass
		
		return cleaned_data


class ExcepcionPersonalForm(forms.ModelForm):
	class Meta:
		model = ExcepcionPersonal
		fields = ['personal', 'fecha_inicio', 'fecha_fin', 'tipo', 'motivo']
		widgets = {
			'personal': forms.Select(attrs={'class': 'form-control'}),
			'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'tipo': forms.Select(attrs={'class': 'form-control'}),
			'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
		}
