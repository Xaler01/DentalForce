"""
Formularios para el módulo de Facturación

Este módulo contiene los formularios para gestión de facturas,
items de factura y pagos con validación multi-tenant.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Factura, ItemFactura, Pago
from pacientes.models import Paciente
from procedimientos.models import ProcedimientoOdontologico


class FacturaForm(forms.ModelForm):
    """
    Formulario para crear/editar facturas
    """
    
    class Meta:
        model = Factura
        fields = [
            'paciente',
            'sucursal',
            'cita',
            'fecha_emision',
            'descuento',
            'iva_porcentaje',
            'observaciones'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'sucursal': forms.Select(attrs={'class': 'form-control'}),
            'cita': forms.Select(attrs={'class': 'form-control'}),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
    
    def __init__(self, *args, clinica=None, paciente=None, **kwargs):
        """
        Inicializa el formulario con filtrado por clínica y paciente
        
        Args:
            clinica: Instancia de Clinica para filtrar opciones
            paciente: Instancia de Paciente para filtrar citas
        """
        super().__init__(*args, **kwargs)
        self.clinica = clinica
        
        if clinica:
            # Filtrar pacientes de la clínica
            self.fields['paciente'].queryset = Paciente.objects.filter(
                clinica=clinica
            )
            
            # Filtrar sucursales de la clínica
            from clinicas.models import Sucursal
            self.fields['sucursal'].queryset = Sucursal.objects.filter(
                clinica=clinica
            )
            
        # Filtrar citas por paciente seleccionado
        if 'cita' in self.fields:
            from cit.models import Cita
            if paciente:
                self.fields['cita'].queryset = Cita.objects.filter(
                    paciente=paciente
                ).order_by('-fecha_hora')
            elif clinica:
                self.fields['cita'].queryset = Cita.objects.filter(
                    paciente__clinica=clinica
                ).order_by('-fecha_hora')
            else:
                self.fields['cita'].queryset = Cita.objects.none()
            self.fields['cita'].required = False
    
    def clean_paciente(self):
        """Valida que el paciente pertenezca a la clínica"""
        paciente = self.cleaned_data.get('paciente')
        
        if paciente and self.clinica:
            if paciente.clinica_id != self.clinica.id:
                raise ValidationError(
                    f"El paciente {paciente} no pertenece a la clínica {self.clinica.nombre}"
                )
        
        return paciente
    
    def clean_descuento(self):
        """Valida que el descuento sea positivo"""
        descuento = self.cleaned_data.get('descuento')
        
        if descuento and descuento < 0:
            raise ValidationError("El descuento no puede ser negativo")
        
        return descuento


class ItemFacturaForm(forms.ModelForm):
    """
    Formulario para agregar items a una factura
    """
    
    class Meta:
        model = ItemFactura
        fields = [
            'procedimiento',
            'descripcion',
            'cantidad',
            'precio_unitario',
            'descuento_item'
        ]
        widgets = {
            'procedimiento': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del servicio...'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer descripción opcional (se llena desde procedimiento)
        self.fields['descripcion'].required = False
        
        # Cargar procedimientos activos
        self.fields['procedimiento'].queryset = ProcedimientoOdontologico.objects.filter(
            estado=True
        ).order_by('nombre')
    
    def clean_cantidad(self):
        """Valida que la cantidad sea positiva"""
        cantidad = self.cleaned_data.get('cantidad')
        
        if cantidad and cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        
        return cantidad
    
    def clean_precio_unitario(self):
        """Valida que el precio sea positivo"""
        precio = self.cleaned_data.get('precio_unitario')
        
        if precio and precio < 0:
            raise ValidationError("El precio no puede ser negativo")
        
        return precio
    
    def clean(self):
        """Validaciones generales"""
        cleaned_data = super().clean()
        procedimiento = cleaned_data.get('procedimiento')
        descripcion = cleaned_data.get('descripcion')
        precio_unitario = cleaned_data.get('precio_unitario')
        
        # Si hay procedimiento pero no descripción, usar nombre del procedimiento
        if procedimiento and not descripcion:
            cleaned_data['descripcion'] = procedimiento.nombre
        
        # Si hay procedimiento pero no precio, usar precio del procedimiento
        if procedimiento and not precio_unitario:
            # Asumiendo que ProcedimientoOdontologico tiene un campo precio
            if hasattr(procedimiento, 'precio_base'):
                cleaned_data['precio_unitario'] = procedimiento.precio_base
        
        return cleaned_data


class ItemFacturaInlineFormSet(forms.BaseInlineFormSet):
    """
    Formset personalizado para items de factura
    """
    
    def clean(self):
        """Valida que haya al menos un item"""
        super().clean()
        
        if any(self.errors):
            return
        
        items_count = sum(
            1 for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        )
        
        if items_count < 1:
            raise ValidationError("Debe agregar al menos un item a la factura")


class PagoForm(forms.ModelForm):
    """
    Formulario para registrar pagos
    """
    
    class Meta:
        model = Pago
        fields = [
            'monto',
            'forma_pago',
            'referencia_pago',
            'observaciones'
        ]
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'forma_pago': forms.Select(attrs={'class': 'form-control'}),
            'referencia_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de referencia, cheque, transacción...'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones del pago...'
            }),
        }
    
    def __init__(self, *args, factura=None, **kwargs):
        """
        Inicializa el formulario con la factura asociada
        
        Args:
            factura: Instancia de Factura para calcular saldo pendiente
        """
        super().__init__(*args, **kwargs)
        self.factura = factura
        
        # Hacer referencia_pago opcional
        self.fields['referencia_pago'].required = False
        self.fields['observaciones'].required = False
        
        # Si hay factura, mostrar saldo pendiente como ayuda
        if factura:
            saldo = factura.total - factura.total_pagado
            self.fields['monto'].help_text = f"Saldo pendiente: ${saldo:.2f}"
    
    def clean_monto(self):
        """Valida que el monto sea positivo y no exceda el saldo"""
        monto = self.cleaned_data.get('monto')
        
        if monto and monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0")
        
        if self.factura and monto:
            saldo_pendiente = self.factura.total - self.factura.total_pagado
            
            if monto > saldo_pendiente:
                raise ValidationError(
                    f"El monto (${monto:.2f}) excede el saldo pendiente (${saldo_pendiente:.2f})"
                )
        
        return monto
    
    def clean_referencia_pago(self):
        """Valida referencia según forma de pago"""
        referencia = self.cleaned_data.get('referencia_pago')
        forma_pago = self.cleaned_data.get('forma_pago')
        
        # Si es transferencia, tarjeta o cheque, la referencia es recomendable
        if forma_pago in [Pago.FORMA_TRANSFERENCIA, Pago.FORMA_TARJETA, Pago.FORMA_CHEQUE]:
            if not referencia:
                raise ValidationError(
                    f"Para pagos con {forma_pago}, se recomienda incluir una referencia"
                )
        
        return referencia


class BuscarFacturaForm(forms.Form):
    """
    Formulario para buscar/filtrar facturas
    """
    
    numero_factura = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'FX-001-00001'
        })
    )
    
    paciente = forms.ModelChoiceField(
        queryset=Paciente.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Factura.ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, clinica=None, **kwargs):
        """Filtrar pacientes por clínica"""
        super().__init__(*args, **kwargs)
        
        if clinica:
            self.fields['paciente'].queryset = Paciente.objects.filter(
                clinica=clinica
            ).order_by('apellidos', 'nombres')
