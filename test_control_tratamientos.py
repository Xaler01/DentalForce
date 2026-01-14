#!/usr/bin/env python
"""
Script de Prueba de Humo - Control de Tratamientos
===================================================

Verifica que el sistema de control de sobre-facturación funcione correctamente.

Escenarios de Prueba:
1. Crear ServicioPendiente con 3 unidades realizadas
2. Intentar facturar 2 unidades → DEBE PASAR
3. Intentar facturar 2 unidades más → DEBE FALLAR (solo 1 disponible)
4. Verificar que cantidad_disponible se actualiza correctamente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from django.contrib.auth import get_user_model
from decimal import Decimal
from facturacion.models import Factura, ItemFactura, ServicioPendiente
from pacientes.models import Paciente
from clinicas.models import Clinica, Sucursal
from procedimientos.models import ProcedimientoOdontologico
from personal.models import Dentista

User = get_user_model()

def print_header(text):
    """Imprime encabezado con formato"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(text, passed=None):
    """Imprime resultado de prueba"""
    if passed is None:
        print(f"\n🔵 TEST: {text}")
    elif passed:
        print(f"✅ PASS: {text}")
    else:
        print(f"❌ FAIL: {text}")

def cleanup_test_data():
    """Limpia datos de pruebas anteriores"""
    print_header("LIMPIEZA DE DATOS DE PRUEBA")
    
    ServicioPendiente.objects.filter(
        descripcion__contains="TEST_CONTROL"
    ).delete()
    print("✅ ServiciosPendientes de prueba eliminados")
    
    ItemFactura.objects.filter(
        descripcion__contains="TEST_CONTROL"
    ).delete()
    print("✅ ItemsFactura de prueba eliminados")
    
    Factura.objects.filter(
        observaciones__contains="TEST_CONTROL"
    ).delete()
    print("✅ Facturas de prueba eliminadas")

def run_smoke_test():
    """Ejecuta prueba de humo completa"""
    
    print_header("INICIO DE PRUEBA DE HUMO - CONTROL DE TRATAMIENTOS")
    
    # Limpiar datos previos
    cleanup_test_data()
    
    # SETUP: Obtener datos existentes
    print_header("CONFIGURACIÓN INICIAL")
    
    clinica = Clinica.objects.first()
    if not clinica:
        print("❌ ERROR: No hay clínicas en la base de datos")
        return False
    print(f"✅ Clínica: {clinica.nombre}")
    
    paciente = Paciente.objects.filter(clinica=clinica).first()
    if not paciente:
        print("❌ ERROR: No hay pacientes en la base de datos")
        return False
    print(f"✅ Paciente: {paciente.get_nombre_completo()}")
    
    procedimiento = ProcedimientoOdontologico.objects.filter(estado=True).first()
    if not procedimiento:
        print("❌ ERROR: No hay procedimientos activos")
        return False
    print(f"✅ Procedimiento: {procedimiento.nombre}")
    
    dentista = Dentista.objects.filter(sucursales__clinica=clinica).first()
    user = User.objects.first()
    sucursal = Sucursal.objects.filter(clinica=clinica).first()
    
    # TEST 1: Crear ServicioPendiente
    print_header("TEST 1: Crear Servicio Pendiente")
    print_test("Crear servicio con 3 unidades realizadas, 0 facturadas")
    
    servicio = ServicioPendiente.objects.create(
        paciente=paciente,
        clinica=clinica,
        dentista=dentista,
        procedimiento=procedimiento,
        cantidad_realizada=3,
        cantidad_facturada=0,
        descripcion="TEST_CONTROL - Prueba de control de sobre-facturación",
        uc=user
    )
    
    if servicio.cantidad_disponible == 3:
        print_test(f"Cantidad disponible: {servicio.cantidad_disponible}", True)
    else:
        print_test(f"Esperado: 3, Obtenido: {servicio.cantidad_disponible}", False)
        return False
    
    # TEST 2: Crear factura y agregar 2 unidades (DEBE PASAR)
    print_header("TEST 2: Facturar 2 unidades (debe pasar)")
    
    factura = Factura.objects.create(
        paciente=paciente,
        clinica=clinica,
        sucursal=sucursal,
        observaciones="TEST_CONTROL - Factura de prueba 1",
        uc=user
    )
    print(f"✅ Factura creada: {factura.numero_factura}")
    
    # Simular agregado de item (2 unidades)
    try:
        item1 = ItemFactura.objects.create(
            factura=factura,
            procedimiento=procedimiento,
            cantidad=2,
            precio_unitario=Decimal('50.00'),
            descuento_item=Decimal('0.00'),
            descripcion=f"TEST_CONTROL - {procedimiento.nombre}",
            uc=user
        )
        
        # La lógica de save() de ItemFactura actualiza automáticamente ServicioPendiente
        servicio.refresh_from_db()
        
        print_test("2 unidades facturadas correctamente", True)
        print(f"   Realizada: {servicio.cantidad_realizada}")
        print(f"   Facturada: {servicio.cantidad_facturada}")
        print(f"   Disponible: {servicio.cantidad_disponible}")
        print(f"   Estado: {servicio.get_estado_display()}")
        
        if servicio.cantidad_disponible != 1:
            print_test(f"ERROR: Disponible debería ser 1, es {servicio.cantidad_disponible}", False)
            return False
            
    except Exception as e:
        print_test(f"Error al facturar 2 unidades: {e}", False)
        return False
    
    # TEST 3: Validación de formulario - intentar facturar 2 más (DEBE FALLAR)
    print_header("TEST 3: Validar sobre-facturación (debe fallar)")
    
    from facturacion.forms import ItemFacturaForm
    
    form_data = {
        'procedimiento': procedimiento.id,
        'cantidad': 2,  # Intentar 2 cuando solo hay 1 disponible
        'precio_unitario': Decimal('50.00'),
        'descuento_item': Decimal('0.00'),
        'descripcion': 'TEST - Sobre-facturación'
    }
    
    form = ItemFacturaForm(data=form_data, factura=factura)
    
    if not form.is_valid():
        print_test("Validación bloqueó correctamente la sobre-facturación", True)
        print(f"   Error del formulario: {form.errors}")
    else:
        print_test("ERROR: El formulario permitió sobre-facturación", False)
        return False
    
    # TEST 4: Facturar la última unidad disponible (DEBE PASAR)
    print_header("TEST 4: Facturar última unidad disponible")
    
    form_data['cantidad'] = 1  # Solo 1 unidad
    form = ItemFacturaForm(data=form_data, factura=factura)
    
    if form.is_valid():
        item2 = form.save(commit=False)
        item2.factura = factura
        item2.uc = user
        item2.save()
        
        # La lógica de save() actualiza automáticamente
        servicio.refresh_from_db()
        
        print_test("Última unidad facturada correctamente", True)
        print(f"   Realizada: {servicio.cantidad_realizada}")
        print(f"   Facturada: {servicio.cantidad_facturada}")
        print(f"   Disponible: {servicio.cantidad_disponible}")
        print(f"   Estado: {servicio.get_estado_display()}")
        
        if servicio.cantidad_disponible != 0:
            print_test(f"ERROR: Disponible debería ser 0, es {servicio.cantidad_disponible}", False)
            return False
            
        if servicio.estado != ServicioPendiente.ESTADO_FACTURADO:
            print_test(f"ERROR: Estado debería ser FACTURADO", False)
            return False
            
    else:
        print_test(f"ERROR: Formulario rechazó facturación válida: {form.errors}", False)
        return False
    
    # TEST 5: Intentar facturar cuando ya está todo facturado (DEBE FALLAR)
    print_header("TEST 5: Validar facturación cuando disponible = 0")
    
    form_data['cantidad'] = 1
    form = ItemFacturaForm(data=form_data, factura=factura)
    
    if not form.is_valid():
        print_test("Validación bloqueó facturación sin disponibilidad", True)
    else:
        print_test("ERROR: El formulario permitió facturar sin disponibilidad", False)
        return False
    
    # LIMPIEZA FINAL
    print_header("LIMPIEZA FINAL")
    cleanup_test_data()
    
    print_header("✅ PRUEBA DE HUMO COMPLETADA EXITOSAMENTE")
    return True

if __name__ == '__main__':
    try:
        success = run_smoke_test()
        if success:
            print("\n" + "🎉"*35)
            print("\n   ✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
            print("\n" + "🎉"*35 + "\n")
            exit(0)
        else:
            print("\n❌ ALGUNAS PRUEBAS FALLARON")
            exit(1)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
