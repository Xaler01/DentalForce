"""
Facturacion app models: Sistema de facturación multi-tenant para PowerDent

Models:
- Factura: Documento de facturación con número secuencial por clínica
- ItemFactura: Ítems individuales de procedimientos en una factura
- Pago: Registro de pagos realizados contra facturas
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from bases.models import ClaseModelo
from pacientes.models import Paciente
from clinicas.models import Clinica, Sucursal
from cit.models import Cita
from procedimientos.models import ProcedimientoOdontologico


class FacturaManager(models.Manager):
    """Manager personalizado para filtrar facturas por clínica"""
    
    def para_clinica(self, clinica_id):
        """Retorna solo facturas de pacientes de la clínica especificada"""
        return self.filter(clinica_id=clinica_id)
    
    def pendientes(self):
        """Retorna solo facturas no pagadas"""
        # ESTADO_PENDIENTE se define en Factura, pero podemos usar el string directo
        return self.filter(estado='PEN')
    
    def pagadas(self):
        """Retorna solo facturas pagadas"""
        return self.filter(estado='PAG')
    
    def pagadas(self):
        """Retorna solo facturas pagadas"""
        return self.filter(estado=Factura.ESTADO_PAGADA)


class Factura(ClaseModelo):
    """
    Modelo de Factura para facturación de servicios odontológicos
    
    Características:
    - Número de factura secuencial por clínica
    - Vinculación con paciente y citas
    - Cálculo automático de IVA
    - Multi-estado (Pendiente, Pagada, Anulada)
    """
    
    # Opciones de Estado
    ESTADO_PENDIENTE = 'PEN'
    ESTADO_PAGADA = 'PAG'
    ESTADO_ANULADA = 'ANU'
    
    ESTADOS_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente de Pago'),
        (ESTADO_PAGADA, 'Pagada'),
        (ESTADO_ANULADA, 'Anulada'),
    ]
    
    # Campos de Facturación
    numero_factura = models.CharField(
        max_length=50,
        verbose_name='Número de Factura',
        help_text='Número secuencial de factura (FX-YYYY-MM-XXXXX)',
        unique=True  # Unique a nivel global para evitar duplicados
    )
    fecha_emision = models.DateField(
        verbose_name='Fecha de Emisión',
        default=timezone.now,
        help_text='Fecha en que se emitió la factura'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='facturas',
        verbose_name='Paciente',
        help_text='Paciente a quien se factura'
    )
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.PROTECT,
        related_name='facturas',
        verbose_name='Clínica',
        help_text='Clínica que emite la factura'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas',
        verbose_name='Sucursal',
        help_text='Sucursal donde se emitió la factura (opcional)'
    )
    cita = models.ForeignKey(
        Cita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas',
        verbose_name='Cita Relacionada',
        help_text='Cita que origina la factura (opcional)'
    )
    
    # Montos
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Subtotal',
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        help_text='Subtotal sin IVA'
    )
    iva_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Porcentaje IVA',
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Porcentaje de IVA a aplicar (0% para servicios de salud en Ecuador)'
    )
    iva_monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='IVA',
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        help_text='Monto de IVA calculado'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Total',
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        help_text='Total con IVA'
    )
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Descuento',
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        blank=True,
        help_text='Descuento aplicado a toda la factura'
    )
    
    # Estado
    estado = models.CharField(
        max_length=3,
        choices=ESTADOS_CHOICES,
        default=ESTADO_PENDIENTE,
        verbose_name='Estado',
        help_text='Estado actual de la factura'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        help_text='Notas u observaciones sobre la factura'
    )
    
    # Manager
    objects = FacturaManager()
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision', '-numero_factura']
        indexes = [
            models.Index(fields=['paciente', 'clinica']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_emision']),
        ]
    
    def __str__(self):
        return f"{self.numero_factura} - {self.paciente} ({self.get_estado_display()})"
    
    @property
    def total_pagado(self):
        """Calcula el total pagado de la factura"""
        # Usar select_related para evitar N+1 queries
        return sum(
            pago.monto for pago in self.pagos.all().select_related()
        ) or Decimal('0.00')
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente de pago"""
        return self.total - self.total_pagado
    
    @property
    def subtotal_neto(self):
        """Subtotal después de aplicar descuento"""
        return self.subtotal - self.descuento
    
    def calcular_totales(self):
        """Recalcula subtotal, IVA y total a partir de ítems"""
        # Sumar items
        self.subtotal = sum(
            item.total for item in self.items.all()
        ) or Decimal('0.00')
        
        # Calcular IVA
        self.iva_monto = (self.subtotal * self.iva_porcentaje) / Decimal('100.00')
        
        # Total con descuento
        total_antes_descuento = self.subtotal + self.iva_monto
        self.total = total_antes_descuento - self.descuento
        
        # Asegurar que no sea negativo
        if self.total < 0:
            self.total = Decimal('0.00')
        
        self.save()
    
    def generar_numero_factura(self):
        """Genera número de factura secuencial por clínica y año"""
        from datetime import datetime
        
        if not self.numero_factura:
            # Contar el total de facturas de esta clínica
            contador = Factura.objects.filter(
                clinica=self.clinica
            ).count() + 1
            
            # Formato: FX-CLINICAID-XXXXX
            self.numero_factura = f"FX-{self.clinica_id}-{contador:05d}"
    
    def save(self, *args, **kwargs):
        """Genera número de factura si no existe"""
        if not self.numero_factura:
            self.generar_numero_factura()
        
        # Validar que paciente y clinica coincidan
        if self.paciente.clinica_id != self.clinica_id:
            raise ValueError(
                f"El paciente {self.paciente} no pertenece a la clínica {self.clinica}"
            )
        
        super().save(*args, **kwargs)
    
    # ==================== MÉTODOS DE VALIDACIÓN PARA EDICIÓN ====================
    
    def tiene_pagos(self):
        """Retorna True si la factura tiene al menos un pago registrado"""
        return self.pagos.exists()
    
    def puede_editar_items(self):
        """
        Retorna True si se pueden editar/eliminar items
        Solo permite edición si NO hay pagos registrados
        """
        return not self.tiene_pagos()
    
    def obtener_motivo_bloqueo(self):
        """Retorna una descripción del motivo por el que está bloqueada"""
        if self.tiene_pagos():
            return f"No se pueden editar items después de registrar pagos. Monto pagado: ${self.total_pagado:.2f}"
        return None


class ItemFactura(ClaseModelo):
    """
    Modelo de Ítem de Factura
    
    Representa un procedimiento o servicio facturado
    """
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Factura',
        help_text='Factura a la que pertenece este ítem'
    )
    procedimiento = models.ForeignKey(
        ProcedimientoOdontologico,
        on_delete=models.PROTECT,
        related_name='items_factura',
        verbose_name='Procedimiento',
        help_text='Procedimiento odontológico facturado'
    )
    cantidad = models.PositiveIntegerField(
        verbose_name='Cantidad',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Cantidad de procedimientos'
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio Unitario',
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Precio por unidad'
    )
    descuento_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Descuento',
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        help_text='Descuento en este ítem'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Total',
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total del ítem (cantidad × precio - descuento)'
    )
    descripcion = models.TextField(
        verbose_name='Descripción',
        blank=True,
        help_text='Descripción adicional del procedimiento'
    )
    
    class Meta:
        verbose_name = 'Ítem de Factura'
        verbose_name_plural = 'Ítems de Factura'
        ordering = ['id']
        indexes = [
            models.Index(fields=['factura']),
        ]
    
    def __str__(self):
        return f"{self.procedimiento} - {self.total}"
    
    def calcular_total(self):
        """Calcula el total del ítem"""
        self.total = (self.cantidad * self.precio_unitario) - self.descuento_item
        if self.total < 0:
            self.total = Decimal('0.00')
        return self.total
    
    def save(self, *args, **kwargs):
        """Calcula total y actualiza factura"""
        self.calcular_total()
        super().save(*args, **kwargs)
        
        # Recalcular totales de la factura
        self.factura.calcular_totales()


class PagoManager(models.Manager):
    """Manager personalizado para filtrar pagos por clínica"""
    
    def para_clinica(self, clinica_id):
        """Retorna solo pagos de facturas de la clínica especificada"""
        return self.filter(factura__clinica_id=clinica_id)


class Pago(ClaseModelo):
    """
    Modelo de Pago
    
    Registro de pagos realizados contra facturas
    """
    
    # Formas de Pago
    FORMA_EFECTIVO = 'EFE'
    FORMA_TARJETA = 'TAR'
    FORMA_TRANSFERENCIA = 'TRA'
    FORMA_CHEQUE = 'CHE'
    FORMA_SEGURO = 'SEG'
    FORMA_OTRO = 'OTR'
    
    FORMAS_PAGO_CHOICES = [
        (FORMA_EFECTIVO, 'Efectivo'),
        (FORMA_TARJETA, 'Tarjeta de Crédito/Débito'),
        (FORMA_TRANSFERENCIA, 'Transferencia Bancaria'),
        (FORMA_CHEQUE, 'Cheque'),
        (FORMA_SEGURO, 'Seguro'),
        (FORMA_OTRO, 'Otro'),
    ]
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name='Factura',
        help_text='Factura que se está pagando'
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Monto',
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Monto pagado'
    )
    fecha_pago = models.DateField(
        verbose_name='Fecha de Pago',
        default=timezone.now,
        help_text='Fecha en que se realizó el pago'
    )
    forma_pago = models.CharField(
        max_length=3,
        choices=FORMAS_PAGO_CHOICES,
        default=FORMA_EFECTIVO,
        verbose_name='Forma de Pago',
        help_text='Forma en que se realizó el pago'
    )
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Referencia',
        help_text='Referencia del pago (número de transacción, cheque, etc.)'
    )
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        help_text='Notas u observaciones sobre el pago'
    )
    
    # Manager
    objects = PagoManager()
    
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['factura']),
            models.Index(fields=['fecha_pago']),
        ]
    
    def __str__(self):
        return f"Pago ${self.monto} - {self.factura.numero_factura} ({self.get_forma_pago_display()})"
    
    def save(self, *args, **kwargs):
        """Actualiza estado de factura si está completamente pagada"""
        super().save(*args, **kwargs)
        
        # Verificar si la factura está totalmente pagada
        total_pagado = sum(
            pago.monto for pago in self.factura.pagos.all()
        ) or Decimal('0.00')
        
        if total_pagado >= self.factura.total:
            self.factura.estado = Factura.ESTADO_PAGADA
            self.factura.save()
