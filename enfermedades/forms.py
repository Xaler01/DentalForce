from django import forms

from .models import CategoriaEnfermedad, Enfermedad, EnfermedadPaciente


class CategoriaEnfermedadForm(forms.ModelForm):
    class Meta:
        model = CategoriaEnfermedad
        fields = ['nombre', 'descripcion', 'icono', 'color', 'orden', 'estado']
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'icono': 'Icono (FontAwesome)',
            'color': 'Color',
            'orden': 'Orden',
            'estado': 'Activo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'maxlength': 100, 'placeholder': 'Cardiovasculares'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción breve de la categoría'}),
            'icono': forms.TextInput(attrs={'placeholder': 'fa-heart'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
            'orden': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            from django.forms import CheckboxInput
            widget = field.widget
            if isinstance(widget, CheckboxInput):
                widget.attrs.update({'class': 'custom-control-input'})
            else:
                widget.attrs.update({'class': 'form-control'})
        self.fields['descripcion'].required = False
        self.fields['icono'].required = False
        self.fields['color'].required = False
        self.fields['orden'].required = False


class EnfermedadForm(forms.ModelForm):
    class Meta:
        model = Enfermedad
        fields = [
            'categoria', 'nombre', 'nombre_cientifico', 'codigo_cie10',
            'descripcion', 'nivel_riesgo', 'contraindicaciones', 'precauciones',
            'requiere_interconsulta', 'genera_alerta_roja', 'genera_alerta_amarilla', 'estado'
        ]
        labels = {
            'categoria': 'Categoría',
            'nombre': 'Nombre',
            'nombre_cientifico': 'Nombre científico',
            'codigo_cie10': 'Código CIE-10',
            'descripcion': 'Descripción',
            'nivel_riesgo': 'Nivel de riesgo',
            'contraindicaciones': 'Contraindicaciones',
            'precauciones': 'Precauciones',
            'requiere_interconsulta': 'Requiere interconsulta',
            'genera_alerta_roja': 'Genera alerta roja',
            'genera_alerta_amarilla': 'Genera alerta amarilla',
            'estado': 'Activo',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción médica'}),
            'contraindicaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Medicamentos o procedimientos contraindicados'}),
            'precauciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Precauciones en procedimientos'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar categorías alfabéticamente
        self.fields['categoria'].queryset = CategoriaEnfermedad.objects.filter(estado=True).order_by('nombre')

        for name, field in self.fields.items():
            from django.forms import CheckboxInput, Select
            widget = field.widget
            if isinstance(widget, CheckboxInput):
                widget.attrs.update({'class': 'custom-control-input'})
            elif isinstance(widget, Select):
                widget.attrs.update({'class': 'form-control custom-select'})
            else:
                widget.attrs.update({'class': 'form-control'})

        # Campos opcionales
        self.fields['nombre_cientifico'].required = False
        self.fields['codigo_cie10'].required = False
        self.fields['descripcion'].required = False
        self.fields['contraindicaciones'].required = False
        self.fields['precauciones'].required = False


class EnfermedadPacienteForm(forms.ModelForm):
    class Meta:
        model = EnfermedadPaciente
        fields = [
            'enfermedad', 'estado_actual', 'fecha_diagnostico',
            'medicacion_actual', 'observaciones', 'requiere_atencion_especial'
        ]
        labels = {
            'enfermedad': 'Enfermedad',
            'estado_actual': 'Estado',
            'fecha_diagnostico': 'Fecha diagnóstico',
            'medicacion_actual': 'Medicación actual',
            'observaciones': 'Observaciones',
            'requiere_atencion_especial': 'Requiere atención especial',
        }
        widgets = {
            'fecha_diagnostico': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'medicacion_actual': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['enfermedad'].queryset = Enfermedad.objects.filter(estado=True).order_by('nombre')
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-control'})
            elif isinstance(widget, forms.DateInput):
                widget.attrs.setdefault('class', 'form-control')
            else:
                widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_diagnostico'].required = False
        self.fields['medicacion_actual'].required = False
        self.fields['observaciones'].required = False
