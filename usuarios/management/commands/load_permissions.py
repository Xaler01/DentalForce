"""
Script para cargar permisos y roles predefinidos en PowerDent

Ejecutar: python manage.py shell < usuarios/management/commands/load_permissions.py
"""
from django.utils import timezone
from usuarios.models import PermisoPersonalizado, RolUsuarioPowerDent

def crear_permisos():
    """Crea los permisos predefinidos del sistema"""
    
    permisos_datos = [
        # RECEPCIÓN
        ('recepcion.ver_citas', 'Ver Citas', 'Permite visualizar el calendario y listado de citas', 'recepcion'),
        ('recepcion.crear_cita', 'Crear Cita', 'Permite crear nuevas citas para pacientes', 'recepcion'),
        ('recepcion.editar_cita', 'Editar Cita', 'Permite editar citas existentes', 'recepcion'),
        ('recepcion.cancelar_cita', 'Cancelar Cita', 'Permite cancelar citas programadas', 'recepcion'),
        ('recepcion.gestionar_pacientes', 'Gestionar Pacientes', 'Permite crear y editar información básica de pacientes', 'recepcion'),
        ('recepcion.ver_historiales', 'Ver Historiales', 'Permite visualizar historiales médicos de pacientes', 'recepcion'),
        
        # ASISTENCIA
        ('asistencia.asistir_procedimiento', 'Asistir Procedimiento', 'Permite asistir en procedimientos odontológicos', 'asistencia'),
        ('asistencia.preparar_instrumentos', 'Preparar Instrumentos', 'Permite preparar y esterilizar instrumentos', 'asistencia'),
        ('asistencia.limpiar_cubiculos', 'Limpiar Cubículos', 'Permite limpiar y desinfectar espacios de trabajo', 'asistencia'),
        ('asistencia.registrar_medicinas', 'Registrar Medicinas', 'Permite registrar uso de medicinas y consumibles', 'asistencia'),
        
        # INVENTARIO
        ('inventario.ver_inventario', 'Ver Inventario', 'Permite visualizar el inventario de materiales', 'inventario'),
        ('inventario.solicitar_inventario', 'Solicitar Inventario', 'Permite solicitar materiales del inventario', 'inventario'),
        
        # ODONTOLOGÍA
        ('odontologia.crear_procedimiento', 'Crear Procedimiento', 'Permite crear registros de procedimientos odontológicos', 'odontologia'),
        ('odontologia.editar_diagnostico', 'Editar Diagnóstico', 'Permite editar diagnósticos en los procedimientos', 'odontologia'),
        ('odontologia.registrar_evolucion', 'Registrar Evolución', 'Permite registrar la evolución del tratamiento', 'odontologia'),
        ('odontologia.prescribir_medicinas', 'Prescribir Medicinas', 'Permite prescribir medicinas a pacientes', 'odontologia'),
        ('odontologia.ver_radiografias', 'Ver Radiografías', 'Permite visualizar radiografías de pacientes', 'odontologia'),
        
        # FACTURACIÓN
        ('facturacion.ver_facturas', 'Ver Facturas', 'Permite visualizar facturas emitidas', 'facturacion'),
        ('facturacion.crear_factura', 'Crear Factura', 'Permite crear nuevas facturas', 'facturacion'),
        ('facturacion.editar_factura', 'Editar Factura', 'Permite editar facturas pendientes', 'facturacion'),
        ('facturacion.anular_factura', 'Anular Factura', 'Permite anular facturas emitidas', 'facturacion'),
        
        # ADMINISTRACIÓN
        ('admin.gestionar_usuarios', 'Gestionar Usuarios', 'Permite crear, editar y desactivar usuarios', 'admin'),
        ('admin.asignar_roles', 'Asignar Roles y Permisos', 'Permite asignar roles y permisos a usuarios', 'admin'),
        ('admin.gestionar_sucursales', 'Gestionar Sucursales', 'Permite crear y editar sucursales', 'admin'),
        
        # REPORTES
        ('reportes.ver_reportes_general', 'Ver Reportes Generales', 'Permite visualizar reportes generales de la clínica', 'reportes'),
        ('reportes.ver_reportes_financiero', 'Ver Reportes Financieros', 'Permite visualizar reportes financieros detallados', 'reportes'),
        ('reportes.exportar_reportes', 'Exportar Reportes', 'Permite exportar reportes a PDF/Excel', 'reportes'),
    ]
    
    permisos_dict = {}
    for codigo, nombre, descripcion, categoria in permisos_datos:
        permiso, created = PermisoPersonalizado.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'categoria': categoria,
                'clinica': None,  # Permiso global
                'activo': True
            }
        )
        permisos_dict[codigo] = permiso
        if created:
            print(f"✅ Permiso creado: {codigo}")
        else:
            print(f"⚠️  Permiso ya existe: {codigo}")
    
    return permisos_dict

def crear_roles(permisos_dict):
    """Crea los roles predefinidos con sus permisos"""
    
    roles_datos = {
        'Recepcionista': {
            'descripcion': 'Personal encargado de recepción y gestión de citas. Acceso limitado a funciones de atención al paciente.',
            'permisos': [
                'recepcion.ver_citas',
                'recepcion.crear_cita',
                'recepcion.editar_cita',
                'recepcion.cancelar_cita',
                'recepcion.gestionar_pacientes',
                'recepcion.ver_historiales',
            ]
        },
        'Auxiliar Odontológico': {
            'descripcion': 'Asiste en procedimientos odontológicos y maneja instrumentos y materiales.',
            'permisos': [
                'asistencia.asistir_procedimiento',
                'asistencia.preparar_instrumentos',
                'asistencia.limpiar_cubiculos',
                'asistencia.registrar_medicinas',
                'inventario.ver_inventario',
                'inventario.solicitar_inventario',
            ]
        },
        'Dentista': {
            'descripcion': 'Profesional odontológico con acceso a historiales, diagnósticos y procedimientos completos.',
            'permisos': [
                'recepcion.ver_citas',
                'odontologia.crear_procedimiento',
                'odontologia.editar_diagnostico',
                'odontologia.registrar_evolucion',
                'odontologia.prescribir_medicinas',
                'odontologia.ver_radiografias',
                'recepcion.ver_historiales',
            ]
        },
        'Recepcionista + Auxiliar': {
            'descripcion': 'Rol combinado para clínicas pequeñas. Combina funciones de recepción y asistencia odontológica.',
            'permisos': [
                # Recepción
                'recepcion.ver_citas',
                'recepcion.crear_cita',
                'recepcion.editar_cita',
                'recepcion.cancelar_cita',
                'recepcion.gestionar_pacientes',
                'recepcion.ver_historiales',
                # Asistencia
                'asistencia.asistir_procedimiento',
                'asistencia.preparar_instrumentos',
                'asistencia.limpiar_cubiculos',
                'asistencia.registrar_medicinas',
                'inventario.ver_inventario',
                'inventario.solicitar_inventario',
            ]
        },
    }
    
    for nombre_rol, datos in roles_datos.items():
        rol, created = RolUsuarioPowerDent.objects.get_or_create(
            nombre=nombre_rol,
            clinica=None,  # Rol global del sistema
            defaults={
                'descripcion': datos['descripcion'],
                'activo': True
            }
        )
        
        # Asignar permisos al rol
        for codigo_permiso in datos['permisos']:
            if codigo_permiso in permisos_dict:
                rol.permisos.add(permisos_dict[codigo_permiso])
        
        if created:
            print(f"✅ Rol creado: {nombre_rol} con {len(datos['permisos'])} permisos")
        else:
            print(f"⚠️  Rol ya existe: {nombre_rol}")

if __name__ == '__main__':
    print("=" * 60)
    print("Cargando permisos y roles predefinidos...")
    print("=" * 60)
    
    permisos = crear_permisos()
    print()
    crear_roles(permisos)
    
    print()
    print("=" * 60)
    print("✅ Permisos y roles cargados exitosamente")
    print("=" * 60)
