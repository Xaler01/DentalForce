"""
Script para cargar permisos y roles predefinidos en PowerDent

Ejecutar: python manage.py load_permissions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import PermisoPersonalizado, RolUsuarioPowerDent


class Command(BaseCommand):
    help = 'Carga permisos y roles predefinidos en el sistema'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Cargando permisos y roles predefinidos...")
        self.stdout.write("=" * 60)
        
        permisos = self.crear_permisos()
        self.stdout.write("")
        self.crear_roles(permisos)
        
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Permisos y roles cargados exitosamente"))
        self.stdout.write("=" * 60)

    def crear_permisos(self):
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
                self.stdout.write(self.style.SUCCESS(f"✅ Permiso creado: {codigo}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Permiso ya existe: {codigo}"))
        
        return permisos_dict

    def crear_roles(self, permisos_dict):
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
            'descripcion': 'Profesional odontológico con acceso a historiales, diagnósticos y procedimientos completos. Puede agendar citas para sus pacientes después de la consulta.',
            'permisos': [
                'recepcion.ver_citas',
                'recepcion.crear_cita',  # Puede agendar próxima cita después de consulta
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
        'Odontólogo Director': {
            'descripcion': 'Para odontólogos que dirigen clínicas nuevas. Acceso completo a: odontología, recepción, facturación e inventario básico. Escalable: cambiar a rol "Dentista" cuando creza el equipo.',
            'permisos': [
                # ODONTOLOGÍA (completo)
                'odontologia.crear_procedimiento',
                'odontologia.editar_diagnostico',
                'odontologia.registrar_evolucion',
                'odontologia.prescribir_medicinas',
                'odontologia.ver_radiografias',
                # RECEPCIÓN (completo)
                'recepcion.ver_citas',
                'recepcion.crear_cita',
                'recepcion.editar_cita',
                'recepcion.cancelar_cita',
                'recepcion.gestionar_pacientes',
                'recepcion.ver_historiales',
                # FACTURACIÓN (completo)
                'facturacion.ver_facturas',
                'facturacion.crear_factura',
                'facturacion.editar_factura',
                'facturacion.anular_factura',
                # INVENTARIO (básico)
                'inventario.ver_inventario',
                'inventario.solicitar_inventario',
                # REPORTES (básico)
                'reportes.ver_reportes_general',
                'reportes.ver_reportes_financiero',
            ]
        },
        'Administrador de Clínica': {
            'descripcion': 'Acceso administrativo completo a la clínica: gestión de usuarios, sucursales, acceso a todos los módulos (citas, pacientes, inventario, facturación, reportes).',
            'permisos': [
                # ADMINISTRACIÓN (completo)
                'admin.gestionar_usuarios',
                'admin.asignar_roles',
                'admin.gestionar_sucursales',
                # RECEPCIÓN (completo)
                'recepcion.ver_citas',
                'recepcion.crear_cita',
                'recepcion.editar_cita',
                'recepcion.cancelar_cita',
                'recepcion.gestionar_pacientes',
                'recepcion.ver_historiales',
                # FACTURACIÓN (completo)
                'facturacion.ver_facturas',
                'facturacion.crear_factura',
                'facturacion.editar_factura',
                'facturacion.anular_factura',
                # INVENTARIO (completo)
                'inventario.ver_inventario',
                'inventario.solicitar_inventario',
                # REPORTES (completo)
                'reportes.ver_reportes_general',
                'reportes.ver_reportes_financiero',
                'reportes.exportar_reportes',
                # ODONTOLOGÍA (lectura para supervisión)
                'odontologia.ver_radiografias',
                'recepcion.ver_historiales',
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
                self.stdout.write(self.style.SUCCESS(f"✅ Rol creado: {nombre_rol} con {len(datos['permisos'])} permisos"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Rol ya existe: {nombre_rol}"))
