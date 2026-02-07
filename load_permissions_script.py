#!/usr/bin/env python
"""
Script para cargar permisos y roles predefinidos en DentalForce
Ejecutar: python manage.py runscript load_initial_permissions
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dentalforce.settings')
django.setup()

from usuarios.models import PermisoPersonalizado, RolUsuarioDentalForce

def run():
    """Carga permisos y roles iniciales"""
    
    print("\n" + "="*70)
    print("CARGANDO PERMISOS Y ROLES PREDEFINIDOS")
    print("="*70 + "\n")
    
    # Definir permisos
    permisos_datos = [
        ('recepcion.ver_citas', 'Ver Citas', 'Permite visualizar el calendario y listado de citas', 'recepcion'),
        ('recepcion.crear_cita', 'Crear Cita', 'Permite crear nuevas citas para pacientes', 'recepcion'),
        ('recepcion.editar_cita', 'Editar Cita', 'Permite editar citas existentes', 'recepcion'),
        ('recepcion.cancelar_cita', 'Cancelar Cita', 'Permite cancelar citas', 'recepcion'),
        ('recepcion.gestionar_pacientes', 'Gestionar Pacientes', 'Permite crear y editar información de pacientes', 'recepcion'),
        ('recepcion.ver_historiales', 'Ver Historiales', 'Permite visualizar historiales de pacientes', 'recepcion'),
        ('asistencia.asistir_procedimiento', 'Asistir Procedimiento', 'Permite asistir en procedimientos odontológicos', 'asistencia'),
        ('asistencia.preparar_instrumentos', 'Preparar Instrumentos', 'Permite preparar y esterilizar instrumentos', 'asistencia'),
        ('asistencia.limpiar_cubiculos', 'Limpiar Cubículos', 'Permite limpiar espacios de trabajo', 'asistencia'),
        ('asistencia.registrar_medicinas', 'Registrar Medicinas', 'Permite registrar uso de medicinas', 'asistencia'),
        ('inventario.ver_inventario', 'Ver Inventario', 'Permite visualizar el inventario', 'inventario'),
        ('inventario.solicitar_inventario', 'Solicitar Inventario', 'Permite solicitar materiales', 'inventario'),
        ('odontologia.crear_procedimiento', 'Crear Procedimiento', 'Permite crear procedimientos odontológicos', 'odontologia'),
        ('odontologia.editar_diagnostico', 'Editar Diagnóstico', 'Permite editar diagnósticos', 'odontologia'),
        ('odontologia.registrar_evolucion', 'Registrar Evolución', 'Permite registrar evolución del tratamiento', 'odontologia'),
        ('odontologia.prescribir_medicinas', 'Prescribir Medicinas', 'Permite prescribir medicinas', 'odontologia'),
        ('odontologia.ver_radiografias', 'Ver Radiografías', 'Permite visualizar radiografías', 'odontologia'),
        ('facturacion.ver_facturas', 'Ver Facturas', 'Permite visualizar facturas', 'facturacion'),
        ('facturacion.crear_factura', 'Crear Factura', 'Permite crear facturas', 'facturacion'),
        ('facturacion.editar_factura', 'Editar Factura', 'Permite editar facturas', 'facturacion'),
        ('facturacion.anular_factura', 'Anular Factura', 'Permite anular facturas', 'facturacion'),
        ('admin.gestionar_usuarios', 'Gestionar Usuarios', 'Permite crear, editar y desactivar usuarios', 'admin'),
        ('admin.asignar_roles', 'Asignar Roles y Permisos', 'Permite asignar roles y permisos', 'admin'),
        ('admin.gestionar_sucursales', 'Gestionar Sucursales', 'Permite crear y editar sucursales', 'admin'),
        ('reportes.ver_reportes_general', 'Ver Reportes Generales', 'Permite visualizar reportes generales', 'reportes'),
        ('reportes.ver_reportes_financiero', 'Ver Reportes Financieros', 'Permite visualizar reportes financieros', 'reportes'),
        ('reportes.exportar_reportes', 'Exportar Reportes', 'Permite exportar reportes', 'reportes'),
    ]
    
    print("Creando permisos...")
    permisos_dict = {}
    for codigo, nombre, descripcion, categoria in permisos_datos:
        permiso, created = PermisoPersonalizado.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'categoria': categoria,
                'clinica': None,
                'activo': True
            }
        )
        permisos_dict[codigo] = permiso
        estado = "✅ Creado" if created else "⚠️  Existente"
        print(f"  {estado}: {codigo}")
    
    print(f"\n✅ Total de permisos: {len(permisos_dict)}\n")
    
    # Definir roles
    print("Creando roles...")
    roles_datos = {
        'Recepcionista': {
            'descripcion': 'Gestiona citas y pacientes. Acceso limitado a recepción.',
            'permisos': [
                'recepcion.ver_citas', 'recepcion.crear_cita', 'recepcion.editar_cita',
                'recepcion.cancelar_cita', 'recepcion.gestionar_pacientes', 'recepcion.ver_historiales'
            ]
        },
        'Auxiliar Odontológico': {
            'descripcion': 'Asiste en procedimientos y maneja materiales e instrumentos.',
            'permisos': [
                'asistencia.asistir_procedimiento', 'asistencia.preparar_instrumentos',
                'asistencia.limpiar_cubiculos', 'asistencia.registrar_medicinas',
                'inventario.ver_inventario', 'inventario.solicitar_inventario'
            ]
        },
        'Dentista': {
            'descripcion': 'Profesional odontológico con acceso completo a procedimientos y diagnósticos.',
            'permisos': [
                'recepcion.ver_citas', 'odontologia.crear_procedimiento',
                'odontologia.editar_diagnostico', 'odontologia.registrar_evolucion',
                'odontologia.prescribir_medicinas', 'odontologia.ver_radiografias',
                'recepcion.ver_historiales'
            ]
        },
        'Recepcionista + Auxiliar': {
            'descripcion': 'Rol combinado para clínicas pequeñas. Combina recepción y asistencia.',
            'permisos': [
                'recepcion.ver_citas', 'recepcion.crear_cita', 'recepcion.editar_cita',
                'recepcion.cancelar_cita', 'recepcion.gestionar_pacientes', 'recepcion.ver_historiales',
                'asistencia.asistir_procedimiento', 'asistencia.preparar_instrumentos',
                'asistencia.limpiar_cubiculos', 'asistencia.registrar_medicinas',
                'inventario.ver_inventario', 'inventario.solicitar_inventario'
            ]
        },
    }
    
    for nombre_rol, datos in roles_datos.items():
        rol, created = RolUsuarioDentalForce.objects.get_or_create(
            nombre=nombre_rol,
            clinica=None,
            defaults={'descripcion': datos['descripcion'], 'activo': True}
        )
        
        # Agregar permisos
        for codigo_permiso in datos['permisos']:
            if codigo_permiso in permisos_dict:
                rol.permisos.add(permisos_dict[codigo_permiso])
        
        estado = "✅ Creado" if created else "⚠️  Existente"
        print(f"  {estado}: {nombre_rol} ({len(datos['permisos'])} permisos)")
    
    print("\n" + "="*70)
    print("✅ PERMISOS Y ROLES CARGADOS EXITOSAMENTE")
    print("="*70 + "\n")

if __name__ == '__main__':
    run()
