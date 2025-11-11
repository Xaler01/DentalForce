from django import forms

from .models import Categoria, SubCategoria, Marca, UnidadMedida, Producto


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['descripcion', 'estado']
        labels = {'descripcion': 'Descripcion de la Categoria',
                  'estado': 'Estado'}
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


class SubCategoriaForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estado=True).order_by('descripcion')
    )

    class Meta:
        model = SubCategoria
        fields = ['categoria', 'descripcion', 'estado']
        labels = {'descripcion': 'Sub categoria',
                  'estado': 'Estado'}
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
        self.fields['categoria'].empty_label = "Seleccione Categoría"


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['descripcion', 'estado']
        labels = {'descripcion': 'Descripcion de la Marca',
                  'estado': 'Estado'}
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


class UMForm(forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = ['descripcion', 'estado']
        labels = {'descripcion': 'Descripcion de la Unidad de Medida',
                  'estado': 'Estado'}
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


class ProductoForm(forms.ModelForm):
    # Campo extra para la categoría (para filtrar subcategorías)
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(estado=True).order_by('descripcion'),
        required=False,
        label='Categoría',
        empty_label="Seleccione Categoría"
    )
    
    class Meta:
        model = Producto
        fields = ['codigo',
                  'codigo_barra',
                  'descripcion',
                  'estado',
                  'precio',
                  'existencia',
                  'ultima_compra',
                  'marca',
                  'subcategoria',
                  'unidad_medida',
                  'cantidad_minima']
        exclude = ['um', 'fm', 'uc', 'fc']
        labels = {'descripcion': 'Descripción del Producto',
                  'estado': 'Estado',
                  'cantidad_minima': 'Cantidad Mínima',
                  'codigo': 'Código',
                  'codigo_barra': 'Código de Barra',
                  'precio': 'Precio',
                  'existencia': 'Existencia',
                  'ultima_compra': 'Última Compra',
                  'marca': 'Marca',
                  'subcategoria': 'Sub Categoría',
                  'unidad_medida': 'Unidad de Medida'}
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
        self.fields['ultima_compra'].widget.attrs['readonly'] = True
        self.fields['existencia'].widget.attrs['readonly'] = True
