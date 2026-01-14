#!/usr/bin/env python
"""
Script de Prueba de Integración - Evolución → ServicioPendiente
================================================================

Verifica que la señal automática cree ServicioPendiente cuando
el odontólogo registra procedimientos en evoluciones.

Escenarios de Prueba:
1. Crear EvolucionConsulta con ProcedimientoEnEvolucion → Debe crear ServicioPendiente automáticamente
2. Verificar que ServicioPendiente tenga los datos correctos
3. Crear otro procedimiento en la misma evolución → Debe crear otro ServicioPendiente
4. Eliminar ProcedimientoEnEvolucion → Debe eliminar/ajustar ServicioPendiente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
django.setup()

from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from facturacion.models import ServicioPendiente
from pacientes.models import Paciente
from clinicas.models import Clinica
from procedimientos.models import ProcedimientoOdontologico
from personal.models import Dentista
from evolucion.models import EvolucionConsulta, ProcedimientoEnEvolucion

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
    
    ProcedimientoEnEvolucion.objects.filter(
        observaciones__contains="TEST_INTEGRACION"
    ).delete()
    print("✅ ProcedimientosEnEvolucion de prueba eliminados")
    
    EvolucionConsulta.objects.filter(
        motivo_consulta__contains="TEST_INTEGRACION"
    ).delete()
    print("✅ Evoluciones de prueba eliminadas")
    
    ServicioPendiente.objects.filter(
        descripcion__contains="TEST_INTEGRACION"
    ).delete()
    print("✅ ServiciosPendientes de prueba eliminados")

def run_integration_test():
    """Ejecuta prueba de integración completa"""
    
    print_header("INICIO DE PRUEBA DE INTEGRACIÓN - EVOLUCIÓN → FACTURACIÓN")
    
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
    
    procedimiento1 = ProcedimientoOdontologico.objects.filter(estado=True).first()
    procedimiento2 = ProcedimientoOdontologico.objects.filter(estado=True).exclude(id=procedimiento1.id).first()
    
    if not procedimiento1 or not procedimiento2:
        print("❌ ERROR: No hay suficientes procedimientos activos")
        return False
    print(f"✅ Procedimiento 1: {procedimiento1.nombre}")
    print(f"✅ Procedimiento 2: {procedimiento2.nombre}")
    
    dentista = Dentista.objects.filter(sucursales__clinica=clinica).first()
    user = User.objects.first()
    
    # TEST 1: Crear Evolución con Procedimiento
    print_header("TEST 1: Crear Evolución con Procedimiento")
    print_test("Crear evolución del paciente con procedimiento realizado")
    
    evolucion = EvolucionConsulta.objects.create(
        paciente=paciente,
        fecha_consulta=date.today(),
        dentista=dentista,
        motivo_consulta="TEST_INTEGRACION - Control dental",
        hallazgos_clinicos="Buen estado general",
        recomendaciones="Continuar higiene",
        uc=user
    )
    print(f"✅ Evolución creada: {evolucion.id}")
    
    # Agregar procedimiento a la evolución
    proc_evol_1 = ProcedimientoEnEvolucion.objects.create(
        evolucion=evolucion,
        procedimiento=procedimiento1,
        cantidad=2,
        observaciones="TEST_INTEGRACION - Procedimiento 1",
        uc=user
    )
    print(f"✅ Procedimiento agregado a evolución: {procedimiento1.nombre} x2")
    
    # Verificar que se creó ServicioPendiente automáticamente
    servicios = ServicioPendiente.objects.filter(
        paciente=paciente,
        procedimiento=procedimiento1,
        fecha_realizacion=date.today()
    )
    
    if servicios.count() == 1:
        print_test("Se creó automáticamente 1 ServicioPendiente", True)
        servicio = servicios.first()
        
        # Verificar datos
        tests_passed = True
        
        if servicio.cantidad_realizada == 2:
            print_test(f"Cantidad realizada: {servicio.cantidad_realizada}", True)
        else:
            print_test(f"ERROR: Esperado 2, Obtenido {servicio.cantidad_realizada}", False)
            tests_passed = False
        
        if servicio.cantidad_facturada == 0:
            print_test(f"Cantidad facturada: {servicio.cantidad_facturada}", True)
        else:
            print_test(f"ERROR: Esperado 0, Obtenido {servicio.cantidad_facturada}", False)
            tests_passed = False
        
        if servicio.cantidad_disponible == 2:
            print_test(f"Cantidad disponible: {servicio.cantidad_disponible}", True)
        else:
            print_test(f"ERROR: Esperado 2, Obtenido {servicio.cantidad_disponible}", False)
            tests_passed = False
        
        if servicio.estado == ServicioPendiente.ESTADO_PENDIENTE:
            print_test(f"Estado: {servicio.get_estado_display()}", True)
        else:
            print_test(f"ERROR: Estado esperado PENDIENTE, obtenido {servicio.get_estado_display()}", False)
            tests_passed = False
        
        if servicio.clinica == clinica:
            print_test(f"Clínica correcta: {servicio.clinica.nombre}", True)
        else:
            print_test(f"ERROR: Clínica incorrecta", False)
            tests_passed = False
        
        if not tests_passed:
            return False
            
    else:
        print_test(f"ERROR: Esperado 1 servicio, obtenido {servicios.count()}", False)
        return False
    
    # TEST 2: Agregar otro procedimiento a la misma evolución
    print_header("TEST 2: Agregar segundo procedimiento a la evolución")
    
    proc_evol_2 = ProcedimientoEnEvolucion.objects.create(
        evolucion=evolucion,
        procedimiento=procedimiento2,
        cantidad=1,
        observaciones="TEST_INTEGRACION - Procedimiento 2",
        uc=user
    )
    print(f"✅ Segundo procedimiento agregado: {procedimiento2.nombre} x1")
    
    # Verificar que se creó otro ServicioPendiente
    servicios_proc2 = ServicioPendiente.objects.filter(
        paciente=paciente,
        procedimiento=procedimiento2,
        fecha_realizacion=date.today()
    )
    
    if servicios_proc2.count() == 1:
        print_test("Se creó automáticamente ServicioPendiente para segundo procedimiento", True)
        servicio2 = servicios_proc2.first()
        
        if servicio2.cantidad_realizada == 1 and servicio2.cantidad_disponible == 1:
            print_test(f"Cantidades correctas: realizada={servicio2.cantidad_realizada}, disponible={servicio2.cantidad_disponible}", True)
        else:
            print_test(f"ERROR: Cantidades incorrectas", False)
            return False
    else:
        print_test(f"ERROR: Esperado 1 servicio, obtenido {servicios_proc2.count()}", False)
        return False
    
    # TEST 3: Verificar que hay 2 servicios pendientes en total
    print_header("TEST 3: Verificar total de servicios pendientes")
    
    total_servicios = ServicioPendiente.objects.filter(
        paciente=paciente,
        fecha_realizacion=date.today()
    ).exclude(descripcion__contains="TEST_CONTROL").count()
    
    if total_servicios == 2:
        print_test(f"Total de servicios pendientes: {total_servicios}", True)
    else:
        print_test(f"ERROR: Esperado 2, obtenido {total_servicios}", False)
        return False
    
    # TEST 4: Eliminar un procedimiento de la evolución
    print_header("TEST 4: Eliminar procedimiento de evolución (sin facturar)")
    
    proc_evol_2.delete()
    print(f"✅ Procedimiento 2 eliminado de la evolución")
    
    # Verificar que se eliminó el ServicioPendiente
    servicios_proc2_after = ServicioPendiente.objects.filter(
        paciente=paciente,
        procedimiento=procedimiento2,
        fecha_realizacion=date.today()
    ).exclude(estado=ServicioPendiente.ESTADO_ANULADO)
    
    if servicios_proc2_after.count() == 0:
        print_test("ServicioPendiente eliminado automáticamente", True)
    else:
        print_test(f"ERROR: El servicio no se eliminó", False)
        return False
    
    # LIMPIEZA FINAL
    print_header("LIMPIEZA FINAL")
    cleanup_test_data()
    
    print_header("✅ PRUEBA DE INTEGRACIÓN COMPLETADA EXITOSAMENTE")
    return True

if __name__ == '__main__':
    try:
        success = run_integration_test()
        if success:
            print("\n" + "🎉"*35)
            print("\n   ✅ INTEGRACIÓN EVOLUCIÓN → FACTURACIÓN FUNCIONANDO")
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
