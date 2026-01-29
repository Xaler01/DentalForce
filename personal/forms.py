from django import forms
from .models import Personal, RegistroHorasPersonal, ExcepcionPersonal


class PersonalForm(forms.ModelForm):
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
	class Meta:
		model = RegistroHorasPersonal
		fields = ['fecha', 'hora_inicio', 'hora_fin', 'tipo_extra', 'observaciones']
		widgets = {
			'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
			'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
			'tipo_extra': forms.Select(attrs={'class': 'form-control'}),
			'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
		}


class ExcepcionPersonalForm(forms.ModelForm):
	class Meta:
		model = ExcepcionPersonal
		fields = ['personal', 'fecha_inicio', 'fecha_fin', 'tipo', 'motivo']
		widgets = {
			'personal': forms.Select(attrs={'class': 'form-control'}),
			'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
			'tipo': forms.Select(attrs={'class': 'form-control'}),
			'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
		}
