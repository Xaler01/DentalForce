from django import forms

from .models import Proveedor, ComprasEnc


class ProveedorForm(forms.ModelForm):
    email = forms.EmailField(max_length=254)

    class Meta:
        model = Proveedor
        exclude = ['um', 'fm', 'uc', 'fc']
        widget = {'descripcion': forms.TextInput}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            from django.forms import CheckboxInput
            widget = field.widget
            if isinstance(widget, CheckboxInput):
                widget.attrs.update({'class': 'custom-control-input'})
            else:
                widget.attrs.update({'class': 'form-control'})


class ComprasEncForm(forms.ModelForm):
    # Use proper DateField with a DateInput widget so validation works correctly
    fecha_compra = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    fecha_factura = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = ComprasEnc
        fields = ['proveedor', 'fecha_compra', 'observacion',
                  'no_factura', 'fecha_factura', 'sub_total',
                  'descuento', 'total']
        widgets = {
            'sub_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # apply default bootstrap classes to widgets when not already set by explicit widget
            if field_name not in ['sub_total', 'descuento', 'total']:
                field.widget.attrs.setdefault('class', 'form-control')
        # make some fields readonly
        if 'fecha_compra' in self.fields:
            self.fields['fecha_compra'].widget.attrs['readonly'] = True
        if 'fecha_factura' in self.fields:
            self.fields['fecha_factura'].widget.attrs['readonly'] = True
