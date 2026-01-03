from django import forms

from .models import CategoriaEnfermedad


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
