from django.db import models

# Create your models here.
from bases.models import ClaseModelo
from inv.models import Producto


class Proveedor(ClaseModelo):
    descripcion = models.CharField(
        max_length=100,
        unique=True
    )
    direccion = models.CharField(
        max_length=250,
        null=True,
        blank=True
    )
    contacto = models.CharField(
        max_length=100
    )
    telefono = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )
    email = models.CharField(
        max_length=250,
        null=True,
    )

    def __str__(self):
        return '{}'.format(self.descripcion)

    def save(self, *args, **kwargs):
        self.descripcion = self.descripcion.upper()
        super(Proveedor, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Proveedores"


class ComprasEnc (ClaseModelo):
    fecha_compra = models.DateField(null=True, blank=True)
    observacion = models.CharField(max_length=250, blank=True, null=True)
    no_factura = models.CharField(max_length=100)
    fecha_factura = models.DateField()
    sub_total = models.FloatField(default=0)
    descuento = models.FloatField(default=0)
    total = models.FloatField(default=0)

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.observacion)

    def save(self, *args, **kwargs):
        if self.observacion:
            self.observacion = self.observacion.upper()
        # Redondeo tradicional a 2 decimales
        self.total = round(float(self.sub_total) - float(self.descuento), 2)
        super(ComprasEnc, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Encabezado Compras"
        verbose_name = "Encabezado Compra"


class ComprasDet (ClaseModelo):
    TIPO_DESCUENTO_CHOICES = [
        ('V', 'Valor'),
        ('P', 'Porcentaje'),
    ]
    
    compra = models.ForeignKey(ComprasEnc, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.BigIntegerField(default=0)
    precio_prv = models.FloatField(default=0)
    sub_total = models.FloatField(default=0)
    descuento = models.FloatField(default=0)
    tipo_descuento = models.CharField(max_length=1, choices=TIPO_DESCUENTO_CHOICES, default='V')
    total = models.FloatField(default=0)
    costo = models.FloatField(default=0)

    def __str__(self):
        return '{}'.format(self.producto)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # Calcular subtotal con redondeo tradicional a 2 decimales
        self.sub_total = round(float(self.cantidad) * float(self.precio_prv), 2)
        
        # Calcular descuento según el tipo con redondeo tradicional
        if self.tipo_descuento == 'P':
            # Si es porcentaje, calcular el valor del descuento
            descuento_calculado = round(self.sub_total * (float(self.descuento) / 100), 2)
        else:
            # Si es valor, usar el descuento directo
            descuento_calculado = round(float(self.descuento), 2)
        
        # Calcular total con redondeo tradicional a 2 decimales
        self.total = round(self.sub_total - descuento_calculado, 2)
        
        # Verificar si es un nuevo registro o una actualización
        is_new = self.pk is None
        
        if not is_new:
            # Si es actualización, obtener la cantidad anterior para ajustar
            old_det = ComprasDet.objects.get(pk=self.pk)
            old_cantidad = old_det.cantidad
            
            # Calcular la diferencia de cantidad
            diferencia = int(self.cantidad) - int(old_cantidad)
            
            # Actualizar existencia del producto
            if diferencia != 0:
                prod = self.producto
                prod.existencia = int(prod.existencia) + diferencia
                prod.ultima_compra = self.compra.fecha_compra
                prod.save()
        else:
            # Si es nuevo registro, aumentar la existencia
            prod = self.producto
            prod.existencia = int(prod.existencia) + int(self.cantidad)
            prod.ultima_compra = self.compra.fecha_compra
            prod.save()
        
        super(ComprasDet, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        # Al eliminar un detalle, restar la cantidad del inventario
        prod = self.producto
        prod.existencia = int(prod.existencia) - int(self.cantidad)
        prod.save()
        
        super(ComprasDet, self).delete(using, keep_parents)

    class Meta:
        verbose_name_plural = "Detalles Compras"
        verbose_name = "Detalle Compra"


