from django.contrib.auth.models import User
from django.test import TestCase
from datetime import date
from decimal import Decimal

from .models import Proveedor, ComprasEnc, ComprasDet
from inv.models import Producto, Categoria, SubCategoria, Marca, UnidadMedida


class ProveedorModelTest(TestCase):
    """
    Pruebas para el modelo Proveedor.
    Verifica que la descripción se convierta a mayúsculas automáticamente.
    """
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.proveedor = Proveedor.objects.create(
            descripcion="Proveedor de Prueba",
            contacto="Juan Pérez",
            telefono="0987654321",
            email="proveedor@test.com",
            uc=self.user
        )

    def test_proveedor_creacion(self):
        """Verifica que el proveedor se cree con descripción en mayúsculas"""
        self.assertEqual(self.proveedor.descripcion, "PROVEEDOR DE PRUEBA")
        self.assertEqual(self.proveedor.contacto, "Juan Pérez")
        self.assertEqual(self.proveedor.telefono, "0987654321")
        self.assertEqual(self.proveedor.email, "proveedor@test.com")

    def test_proveedor_str(self):
        """Verifica que el método __str__ retorne la descripción"""
        self.assertEqual(str(self.proveedor), "PROVEEDOR DE PRUEBA")

    def test_proveedor_direccion_opcional(self):
        """Verifica que la dirección sea opcional"""
        proveedor_sin_direccion = Proveedor.objects.create(
            descripcion="Proveedor Sin Dirección",
            contacto="María López",
            uc=self.user
        )
        self.assertIsNone(proveedor_sin_direccion.direccion)


class ComprasEncModelTest(TestCase):
    """
    Pruebas para el modelo ComprasEnc (Encabezado de Compras).
    Verifica cálculos de totales y conversión a mayúsculas de observación.
    """
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.proveedor = Proveedor.objects.create(
            descripcion="Proveedor Test",
            contacto="Test Contact",
            uc=self.user
        )
        self.compra = ComprasEnc.objects.create(
            fecha_compra=date(2025, 11, 1),
            observacion="Compra de Prueba",
            no_factura="001-001-0000001",
            fecha_factura=date(2025, 11, 1),
            sub_total=1000.0,
            descuento=100.0,
            proveedor=self.proveedor,
            uc=self.user
        )

    def test_compra_creacion(self):
        """Verifica que la compra se cree correctamente"""
        self.assertEqual(self.compra.observacion, "COMPRA DE PRUEBA")
        self.assertEqual(self.compra.no_factura, "001-001-0000001")
        self.assertEqual(self.compra.proveedor.descripcion, "PROVEEDOR TEST")

    def test_compra_calculo_total(self):
        """Verifica que el total se calcule automáticamente (sub_total - descuento)"""
        self.assertEqual(self.compra.total, 900.0)

    def test_compra_str(self):
        """Verifica que el método __str__ retorne la observación"""
        self.assertEqual(str(self.compra), "COMPRA DE PRUEBA")

    def test_compra_sin_descuento(self):
        """Verifica compra sin descuento"""
        compra_sin_descuento = ComprasEnc.objects.create(
            fecha_compra=date(2025, 11, 2),
            observacion="Compra Sin Descuento",
            no_factura="001-001-0000002",
            fecha_factura=date(2025, 11, 2),
            sub_total=500.0,
            descuento=0.0,
            proveedor=self.proveedor,
            uc=self.user
        )
        self.assertEqual(compra_sin_descuento.total, 500.0)

    def test_compra_observacion_opcional(self):
        """Verifica que la observación sea opcional"""
        compra_sin_obs = ComprasEnc.objects.create(
            fecha_compra=date(2025, 11, 3),
            no_factura="001-001-0000003",
            fecha_factura=date(2025, 11, 3),
            sub_total=200.0,
            proveedor=self.proveedor,
            uc=self.user
        )
        self.assertIsNone(compra_sin_obs.observacion)


class ComprasDetModelTest(TestCase):
    """
    Pruebas para el modelo ComprasDet (Detalle de Compras).
    Verifica cálculos de subtotales, totales y actualización de inventario.
    """
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create(username="testuser")
        
        # Crear datos de inventario necesarios
        self.categoria = Categoria.objects.create(
            descripcion="Categoria Test",
            uc=self.user
        )
        self.subcategoria = SubCategoria.objects.create(
            categoria=self.categoria,
            descripcion="Subcategoria Test",
            uc=self.user
        )
        self.marca = Marca.objects.create(
            descripcion="Marca Test",
            uc=self.user
        )
        self.unidad_medida = UnidadMedida.objects.create(
            descripcion="Unidad Test",
            uc=self.user
        )
        self.producto = Producto.objects.create(
            codigo="PROD001",
            descripcion="Producto Test",
            precio=100.0,
            existencia=0,  # Iniciamos en 0 para ver el incremento
            marca=self.marca,
            unidad_medida=self.unidad_medida,
            subcategoria=self.subcategoria,
            uc=self.user
        )
        
        # Crear proveedor y compra
        self.proveedor = Proveedor.objects.create(
            descripcion="Proveedor Test",
            contacto="Test Contact",
            uc=self.user
        )
        self.compra = ComprasEnc.objects.create(
            fecha_compra=date(2025, 11, 1),
            observacion="Compra Test",
            no_factura="001-001-0000001",
            fecha_factura=date(2025, 11, 1),
            proveedor=self.proveedor,
            uc=self.user
        )

    def test_detalle_creacion(self):
        """Verifica que el detalle se cree correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=0.0,
            uc=self.user
        )
        self.assertEqual(detalle.cantidad, 10)
        self.assertEqual(detalle.precio_prv, 50.0)
        self.assertEqual(str(detalle), "PRODUCTO TEST")

    def test_detalle_calculo_subtotal(self):
        """Verifica que el subtotal se calcule automáticamente (cantidad * precio_prv)"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=0.0,
            uc=self.user
        )
        self.assertEqual(detalle.sub_total, 500.0)

    def test_detalle_calculo_total(self):
        """Verifica que el total se calcule correctamente (sub_total - descuento)"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=50.0,
            uc=self.user
        )
        self.assertEqual(detalle.total, 450.0)

    def test_detalle_actualiza_inventario(self):
        """Verifica que al crear un detalle, se actualice la existencia del producto"""
        existencia_inicial = self.producto.existencia
        
        ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=20,
            precio_prv=50.0,
            descuento=0.0,
            uc=self.user
        )
        
        # Refrescar producto desde la BD
        self.producto.refresh_from_db()
        
        # La existencia debe haber aumentado en 20
        self.assertEqual(self.producto.existencia, existencia_inicial + 20)

    def test_detalle_actualiza_ultima_compra(self):
        """Verifica que se actualice la fecha de última compra del producto"""
        ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            precio_prv=100.0,
            uc=self.user
        )
        
        # Refrescar producto desde la BD
        self.producto.refresh_from_db()
        
        # La última compra debe ser la fecha de la compra
        self.assertEqual(self.producto.ultima_compra, self.compra.fecha_compra)

    def test_detalle_delete_reduce_inventario(self):
        """Verifica que al eliminar un detalle, se reduzca la existencia del producto"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=15,
            precio_prv=50.0,
            uc=self.user
        )
        
        # Refrescar producto
        self.producto.refresh_from_db()
        existencia_con_compra = self.producto.existencia
        
        # Eliminar el detalle
        detalle.delete()
        
        # Refrescar producto nuevamente
        self.producto.refresh_from_db()
        
        # La existencia debe haber disminuido en 15
        self.assertEqual(self.producto.existencia, existencia_con_compra - 15)

    def test_detalle_update_actualiza_inventario(self):
        """Verifica que al actualizar un detalle, se ajuste la existencia correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            uc=self.user
        )
        
        # Refrescar producto
        self.producto.refresh_from_db()
        existencia_inicial = self.producto.existencia
        
        # Actualizar cantidad del detalle
        detalle.cantidad = 25  # Aumentamos de 10 a 25 (+15)
        detalle.save()
        
        # Refrescar producto
        self.producto.refresh_from_db()
        
        # La existencia debe haber aumentado en 15 unidades más
        self.assertEqual(self.producto.existencia, existencia_inicial + 15)


class ComprasDetDescuentosTest(TestCase):
    """
    Pruebas para el sistema de descuentos en ComprasDet.
    Verifica el cálculo correcto de descuentos por valor y porcentaje.
    """
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create(username="testuser")
        
        # Crear datos de inventario necesarios
        self.categoria = Categoria.objects.create(
            descripcion="Categoria Test",
            uc=self.user
        )
        self.subcategoria = SubCategoria.objects.create(
            categoria=self.categoria,
            descripcion="Subcategoria Test",
            uc=self.user
        )
        self.marca = Marca.objects.create(
            descripcion="Marca Test",
            uc=self.user
        )
        self.unidad_medida = UnidadMedida.objects.create(
            descripcion="Unidad Test",
            uc=self.user
        )
        self.producto = Producto.objects.create(
            codigo="PROD001",
            descripcion="Producto Test",
            precio=100.0,
            existencia=0,
            marca=self.marca,
            unidad_medida=self.unidad_medida,
            subcategoria=self.subcategoria,
            uc=self.user
        )
        
        # Crear proveedor y compra
        self.proveedor = Proveedor.objects.create(
            descripcion="Proveedor Test",
            contacto="Test Contact",
            uc=self.user
        )
        self.compra = ComprasEnc.objects.create(
            fecha_compra=date(2025, 11, 1),
            observacion="Compra Test Descuentos",
            no_factura="001-001-0000001",
            fecha_factura=date(2025, 11, 1),
            proveedor=self.proveedor,
            uc=self.user
        )

    def test_descuento_por_valor(self):
        """Verifica que el descuento por valor se calcule correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=75.0,
            tipo_descuento='V',  # Valor
            uc=self.user
        )
        
        # Subtotal = 10 * 50 = 500
        self.assertEqual(detalle.sub_total, 500.0)
        # Descuento = 75 (valor fijo)
        # Total = 500 - 75 = 425
        self.assertEqual(detalle.total, 425.0)

    def test_descuento_por_porcentaje(self):
        """Verifica que el descuento por porcentaje se calcule correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=20,
            precio_prv=100.0,
            descuento=10.0,  # 10%
            tipo_descuento='P',  # Porcentaje
            uc=self.user
        )
        
        # Subtotal = 20 * 100 = 2000
        self.assertEqual(detalle.sub_total, 2000.0)
        # Descuento = 2000 * 10% = 200
        # Total = 2000 - 200 = 1800
        self.assertEqual(detalle.total, 1800.0)

    def test_descuento_porcentaje_redondeo(self):
        """Verifica que el descuento por porcentaje se redondee correctamente a 2 decimales"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=18,
            precio_prv=23.34,
            descuento=8.03,  # 8.03%
            tipo_descuento='P',  # Porcentaje
            uc=self.user
        )
        
        # Subtotal = 18 * 23.34 = 420.12
        self.assertEqual(detalle.sub_total, 420.12)
        # Descuento = 420.12 * 8.03% = 33.73656 → 33.74 (redondeado)
        # Total = 420.12 - 33.74 = 386.38
        self.assertEqual(round(detalle.total, 2), 386.38)

    def test_descuento_sin_descuento(self):
        """Verifica que funcione correctamente sin descuento"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=5,
            precio_prv=100.0,
            descuento=0.0,
            tipo_descuento='V',
            uc=self.user
        )
        
        # Subtotal = 5 * 100 = 500
        self.assertEqual(detalle.sub_total, 500.0)
        # Sin descuento
        # Total = 500
        self.assertEqual(detalle.total, 500.0)

    def test_descuento_porcentaje_100(self):
        """Verifica que el descuento del 100% funcione correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=100.0,  # 100%
            tipo_descuento='P',
            uc=self.user
        )
        
        # Subtotal = 10 * 50 = 500
        self.assertEqual(detalle.sub_total, 500.0)
        # Descuento = 500 * 100% = 500
        # Total = 500 - 500 = 0
        self.assertEqual(detalle.total, 0.0)

    def test_descuento_tipo_default(self):
        """Verifica que el tipo de descuento por defecto sea 'V' (Valor)"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=50.0,
            descuento=50.0,
            # No especificamos tipo_descuento, debe ser 'V' por defecto
            uc=self.user
        )
        
        self.assertEqual(detalle.tipo_descuento, 'V')
        # Como es tipo 'V', el descuento es el valor directo (50)
        # Total = 500 - 50 = 450
        self.assertEqual(detalle.total, 450.0)

    def test_descuento_cambio_de_tipo(self):
        """Verifica que al cambiar el tipo de descuento, se recalcule correctamente"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=10,
            precio_prv=100.0,
            descuento=10.0,
            tipo_descuento='V',  # Primero como valor
            uc=self.user
        )
        
        # Con tipo 'V': Total = 1000 - 10 = 990
        self.assertEqual(detalle.total, 990.0)
        
        # Cambiar a porcentaje
        detalle.tipo_descuento = 'P'
        detalle.save()
        
        # Con tipo 'P': Total = 1000 - (1000 * 10%) = 1000 - 100 = 900
        self.assertEqual(detalle.total, 900.0)

    def test_descuento_precision_decimal(self):
        """Verifica la precisión de 2 decimales en los cálculos"""
        detalle = ComprasDet.objects.create(
            compra=self.compra,
            producto=self.producto,
            cantidad=11,
            precio_prv=3.06,
            descuento=30.0,  # 30%
            tipo_descuento='P',
            uc=self.user
        )
        
        # Subtotal = 11 * 3.06 = 33.66
        self.assertEqual(detalle.sub_total, 33.66)
        # Descuento = 33.66 * 30% = 10.098 → 10.10 (redondeado)
        # Total = 33.66 - 10.10 = 23.56
        self.assertAlmostEqual(detalle.total, 23.56, places=2)
