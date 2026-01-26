"""
Forms para gestión de procedimientos odontológicos y precios por clínica.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import ProcedimientoOdontologico, ClinicaProcedimiento
from clinicas.models import Clinica


class ProcedimientoOdontologicoForm(forms.ModelForm):
    """Formulario para crear/editar procedimientos odontológicos"""
    
    class Meta:
        model = ProcedimientoOdontologico
        fields = [
            'codigo',
            'codigo_cdt',
            'nombre',
            'descripcion',
            'categoria',
            'duracion_estimada',
            'requiere_anestesia',
            'afecta_odontograma',
            'estado'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: RES-OBT001'
            }),
            'codigo_cdt': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: D2140 (opcional)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del procedimiento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del procedimiento'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'duracion_estimada': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutos',
                'min': '5'
            }),
            'requiere_anestesia': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'afecta_odontograma': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'codigo': 'Código',
            'codigo_cdt': 'Código CDT',
            'nombre': 'Nombre del Procedimiento',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'duracion_estimada': 'Duración Estimada (minutos)',
            'requiere_anestesia': '¿Requiere Anestesia?',
            'afecta_odontograma': '¿Afecta Odontograma?',
            'estado': 'Activo'
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper().strip()
            # Verificar que sea único (excepto en edición)
            qs = ProcedimientoOdontologico.objects.filter(codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f'El código {codigo} ya está en uso.')
        return codigo
    
    def clean_duracion_estimada(self):
        duracion = self.cleaned_data.get('duracion_estimada')
        if duracion and duracion < 5:
            raise ValidationError('La duración mínima es de 5 minutos.')
        return duracion


class ClinicaProcedimientoForm(forms.ModelForm):
    """Formulario para asignar precios de procedimientos por clínica"""
    
    class Meta:
        model = ClinicaProcedimiento
        fields = [
            'clinica',
            'procedimiento',
            'precio',
            'moneda',
            'descuento_porcentaje',
            'activo',
            'notas'
        ]
        widgets = {
            'clinica': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'procedimiento': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'moneda': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'USD',
                'maxlength': '3'
            }),
            'descuento_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas adicionales sobre el precio (opcional)'
            })
        }
        labels = {
            'clinica': 'Clínica',
            'procedimiento': 'Procedimiento',
            'precio': 'Precio',
            'moneda': 'Moneda',
            'descuento_porcentaje': 'Descuento (%)',
            'activo': 'Activo',
            'notas': 'Notas'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si el usuario tiene una clínica asignada, filtrar solo su clínica y deshabilitar campo
        if user:
            from usuarios.models import UsuarioClinica
            try:
                usuario_clinica = UsuarioClinica.objects.get(usuario=user, activo=True)
                clinica_usuario = usuario_clinica.clinica
                
                # Filtrar solo su clínica
                self.fields['clinica'].queryset = Clinica.objects.filter(
                    id=clinica_usuario.id,
                    estado=True
                )
                # Preseleccionar y deshabilitar (solo lectura)
                self.fields['clinica'].initial = clinica_usuario
                self.fields['clinica'].disabled = True  # No puede cambiar de clínica
                
            except UsuarioClinica.DoesNotExist:
                # Si no tiene clínica asignada, mostrar solo clínicas activas
                self.fields['clinica'].queryset = Clinica.objects.filter(estado=True)
        else:
            # Si no hay usuario, mostrar todas las clínicas activas
            self.fields['clinica'].queryset = Clinica.objects.filter(estado=True)
        
        # Filtrar solo procedimientos activos
        self.fields['procedimiento'].queryset = ProcedimientoOdontologico.objects.filter(
            estado=True
        ).order_by('categoria', 'nombre')
    
    def clean(self):
        cleaned_data = super().clean()
        clinica = cleaned_data.get('clinica')
        procedimiento = cleaned_data.get('procedimiento')
        
        # Validar que no exista otro precio activo para esta combinación
        if clinica and procedimiento:
            qs = ClinicaProcedimiento.objects.filter(
                clinica=clinica,
                procedimiento=procedimiento,
                activo=True
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f'Ya existe un precio activo para {procedimiento.nombre} en {clinica.nombre}. '
                    f'Desactive el anterior antes de crear uno nuevo.'
                )
        
        return cleaned_data
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio
    
    def clean_descuento_porcentaje(self):
        descuento = self.cleaned_data.get('descuento_porcentaje')
        if descuento is not None:
            if descuento < 0 or descuento > 100:
                raise ValidationError('El descuento debe estar entre 0 y 100%.')
        return descuento
