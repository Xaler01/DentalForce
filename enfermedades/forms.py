from django import forms

from .models import CategoriaEnfermedad, Enfermedad


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
