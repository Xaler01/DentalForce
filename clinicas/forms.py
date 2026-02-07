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
    
    def __init__(self, *args, **kwargs):
        # Extraer el usuario del kwargs si viene
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Guardar el usuario para usarlo en clean_clinica
        self._user = user
        
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
                        self.fields['clinica'].queryset = Clinica.objects.all()
                except Exception as e:
                    # Si hay error, usar comportamiento por defecto
                    self.fields['clinica'].queryset = Clinica.objects.all()
            else:
                # Para superusers: mostrar todas las clínicas
                self.fields['clinica'].queryset = Clinica.objects.all()
        else:
            # Si no viene user, mostrar todas (fallback)
            self.fields['clinica'].queryset = Clinica.objects.all()
    
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
