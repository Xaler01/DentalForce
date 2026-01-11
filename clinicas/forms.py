from django import forms
from django.core.exceptions import ValidationError
from .models import Clinica, Sucursal, Especialidad, Cubiculo


class ClinicaForm(forms.ModelForm):
    """Formulario para crear/editar Clínicas"""
    class Meta:
        model = Clinica
        fields = [
            'nombre', 'direccion', 'telefono', 'email',
            'eslogan', 'titulo_pestana',
            'ruc', 'razon_social', 'representante_legal',
            'pais', 'moneda', 'zona_horaria',
            'logo', 'sitio_web'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la Clínica'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1-234-567-8900'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@clinica.com'}),
            'eslogan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Eslogan corto (máx. 80 caracteres)'}),
            'titulo_pestana': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUC/NIT/CUIT'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Representante Legal'}),
            'pais': forms.Select(attrs={'class': 'form-control'}),
            'moneda': forms.Select(attrs={'class': 'form-control'}),
            'zona_horaria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'America/Guayaquil'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.clinica.com'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono or len(telefono.strip()) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 caracteres')
        return telefono


class SucursalForm(forms.ModelForm):
    """Formulario para crear/editar Sucursales"""
    class Meta:
        model = Sucursal
        fields = [
            'clinica', 'nombre', 'direccion', 'telefono', 'email',
            'horario_apertura', 'horario_cierre', 'dias_atencion',
            'sabado_horario_apertura', 'sabado_horario_cierre',
            'domingo_horario_apertura', 'domingo_horario_cierre'
        ]
        widgets = {
            'clinica': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la Sucursal'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1-234-567-8900'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'sucursal@clinica.com'}),
            'horario_apertura': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_cierre': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'dias_atencion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lunes a Viernes'}),
            'sabado_horario_apertura': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sabado_horario_cierre': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'domingo_horario_apertura': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'domingo_horario_cierre': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class EspecialidadForm(forms.ModelForm):
    """Formulario para crear/editar Especialidades"""
    class Meta:
        model = Especialidad
        fields = ['nombre', 'descripcion', 'duracion_default', 'color_calendario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ortodoncia, Endodoncia'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada'}),
            'duracion_default': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duración en minutos', 'min': 15}),
            'color_calendario': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'type': 'color',
                    'placeholder': '#3498db'
                }
            ),
        }


class CubiculoForm(forms.ModelForm):
    """Formulario para crear/editar Cubículos"""
    class Meta:
        model = Cubiculo
        fields = ['sucursal', 'nombre', 'descripcion', 'numero', 'capacidad', 'equipamiento']
        widgets = {
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Consultorio 1, Sala de Cirugía'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción breve'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número identificador', 'min': 1}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de personas', 'min': 1}),
            'equipamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción del equipamiento'}),
        }
