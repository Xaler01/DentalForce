"""
Forms para el módulo de Pacientes (SOOD-46)
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Paciente
from enfermedades.models import Enfermedad


class PacienteForm(forms.ModelForm):
    """Formulario para crear/editar pacientes"""
    
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date'
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d'],
        label='Fecha de Nacimiento'
    )
    
    foto = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text='Foto opcional del paciente (JPG, PNG)'
    )
    
    class Meta:
        model = Paciente
        fields = [
            'nombres', 'apellidos', 'cedula', 'fecha_nacimiento', 'genero',
            'telefono', 'email', 'direccion',
            'tipo_sangre', 'alergias', 'observaciones_medicas',
            'enfermedades', 'es_vip', 'categoria_vip',
            'contacto_emergencia_nombre', 'contacto_emergencia_telefono',
            'contacto_emergencia_relacion', 'foto', 'clinica'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1234567890 o 1234567890-0',
                'maxlength': '20'
            }),
            'genero': forms.Select(attrs={
                'class': 'form-control'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono',
                'type': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@ejemplo.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección de domicilio'
            }),
            'tipo_sangre': forms.Select(attrs={
                'class': 'form-control'
            }),
            'alergias': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Alergias conocidas (si las hay)'
            }),
            'observaciones_medicas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Condiciones médicas, medicamentos actuales, etc.'
            }),
            'enfermedades': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '6'
            }),
            'es_vip': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'categoria_vip': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contacto_emergencia_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto'
            }),
            'contacto_emergencia_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de emergencia',
                'type': 'tel'
            }),
            'contacto_emergencia_relacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Madre, Esposo, Hermano'
            }),
            'clinica': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'cedula': 'Cédula/DNI',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'genero': 'Género',
            'telefono': 'Teléfono',
            'email': 'Email',
            'direccion': 'Dirección',
            'tipo_sangre': 'Tipo de Sangre',
            'alergias': 'Alergias',
            'observaciones_medicas': 'Observaciones Médicas',
            'enfermedades': 'Enfermedades (selección asistida)',
            'contacto_emergencia_nombre': 'Nombre Contacto Emergencia',
            'contacto_emergencia_telefono': 'Teléfono Emergencia',
            'contacto_emergencia_relacion': 'Relación',
            'foto': 'Fotografía',
            'clinica': 'Clínica',
            'es_vip': 'Cliente VIP',
            'categoria_vip': 'Categoría VIP',
        }

    enfermedades = forms.ModelMultipleChoiceField(
        queryset=Enfermedad.objects.filter(estado=True).order_by('nombre'),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '8'
        }),
        label='Enfermedades (catálogo)',
        help_text='Selecciona una o varias del catálogo (usa Ctrl/Cmd para múltiples)'
    )
    
    def clean_cedula(self):
        """Validar cédula ecuatoriana única"""
        cedula = self.cleaned_data.get('cedula', '').strip()
        
        if not cedula:
            raise ValidationError('La cédula es obligatoria')
        
        # Validar formato: solo números y guiones
        if not re.match(r'^[0-9\-]+$', cedula):
            raise ValidationError('La cédula solo puede contener números y guiones')
        
        # Remover guiones para verificar unicidad
        cedula_sin_guiones = cedula.replace('-', '')
        
        # Verificar que sea única (excepto en edición)
        qs_activos = Paciente.objects.filter(cedula=cedula, estado=True)
        if self.instance.pk:
            qs_activos = qs_activos.exclude(pk=self.instance.pk)
        
        if qs_activos.exists():
            raise ValidationError('Ya existe un paciente activo con esta cédula')
        
        # Detectar duplicados inactivos para guiar a reactivación
        qs_inactivos = Paciente.objects.filter(cedula=cedula, estado=False)
        if self.instance.pk:
            qs_inactivos = qs_inactivos.exclude(pk=self.instance.pk)
        if qs_inactivos.exists():
            raise ValidationError('Existe un paciente desactivado con esta cédula. Incluye inactivos en la lista y reactívalo.')
        
        return cedula
    
    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email', '').strip()
        
        if email:
            qs_activos = Paciente.objects.filter(email=email, estado=True)
            if self.instance.pk:
                qs_activos = qs_activos.exclude(pk=self.instance.pk)
            
            if qs_activos.exists():
                raise ValidationError('Ya existe un paciente activo con este email')
            
            qs_inactivos = Paciente.objects.filter(email=email, estado=False)
            if self.instance.pk:
                qs_inactivos = qs_inactivos.exclude(pk=self.instance.pk)
            if qs_inactivos.exists():
                raise ValidationError('Existe un paciente desactivado con este email. Incluye inactivos en la lista y reactívalo.')
        
        return email
    
    def clean_telefono(self):
        """Validar teléfono"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if telefono and len(telefono) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos')
        
        return telefono
    
    def clean_contacto_emergencia_telefono(self):
        """Validar teléfono de emergencia"""
        telefono = self.cleaned_data.get('contacto_emergencia_telefono', '').strip()
        nombre = self.cleaned_data.get('contacto_emergencia_nombre', '').strip()
        
        if nombre and not telefono:
            raise ValidationError('Si especifica un contacto de emergencia, debe incluir su teléfono')
        
        if telefono and len(telefono) < 7:
            raise ValidationError('El teléfono de emergencia debe tener al menos 7 dígitos')
        
        return telefono


class PacienteBuscarForm(forms.Form):
    """Formulario para búsqueda y filtrado de pacientes"""
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, cédula o teléfono...',
            'id': 'id_buscar'
        }),
        label='Buscar'
    )
    
    genero = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los géneros')] + Paciente.GENERO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_genero'
        }),
        label='Género'
    )
    
    tipo_sangre = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + Paciente.TIPO_SANGRE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_tipo_sangre'
        }),
        label='Tipo de Sangre'
    )
