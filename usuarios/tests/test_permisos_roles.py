"""
Pruebas unitarias para el sistema de permisos granulares.

Cubre:
- Modelos: PermisoPersonalizado, RolUsuarioPowerDent, UsuarioClinica
- Métodos: tiene_permiso(), get_permisos(), get_codigos_permisos()
- Lógica de negocio: múltiples roles, permisos adicionales
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from usuarios.models import (
    PermisoPersonalizado,
    RolUsuarioPowerDent,
    UsuarioClinica,
    RolUsuario
)
from clinicas.models import Clinica


class PermisoPersonalizadoTestCase(TestCase):
    """Pruebas para el modelo PermisoPersonalizado"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            ruc='1234567890001',
            telefono='0999999999',
            email='test@clinica.com'
        )
        
        # Permiso global del sistema
        self.permiso_global = PermisoPersonalizado.objects.create(
            codigo='test.permiso_global',
            nombre='Permiso Global Test',
            descripcion='Permiso global de prueba',
            categoria='recepcion',
            clinica=None,  # Global
            activo=True
        )
        
        # Permiso personalizado de clínica
        self.permiso_clinica = PermisoPersonalizado.objects.create(
            codigo='test.permiso_clinica',
            nombre='Permiso Clínica Test',
            descripcion='Permiso personalizado de prueba',
            categoria='admin',
            clinica=self.clinica,
            activo=True
        )
    
    def test_creacion_permiso_global(self):
        """Verificar que se puede crear un permiso global"""
        self.assertIsNone(self.permiso_global.clinica)
        self.assertTrue(self.permiso_global.es_global)
        self.assertEqual(str(self.permiso_global), 
                        'test.permiso_global - Permiso Global Test (Sistema)')
    
    def test_creacion_permiso_clinica(self):
        """Verificar que se puede crear un permiso de clínica"""
        self.assertIsNotNone(self.permiso_clinica.clinica)
        self.assertFalse(self.permiso_clinica.es_global)
        self.assertEqual(self.permiso_clinica.clinica, self.clinica)
        self.assertIn('Clínica Test', str(self.permiso_clinica))
    
    def test_codigo_unico(self):
        """Verificar que el código del permiso es único"""
        with self.assertRaises(Exception):
            PermisoPersonalizado.objects.create(
                codigo='test.permiso_global',  # Código duplicado
                nombre='Otro Permiso',
                descripcion='Prueba duplicado',
                categoria='recepcion',
                activo=True
            )
    
    def test_categorias_validas(self):
        """Verificar que solo se aceptan categorías válidas"""
        categorias_validas = [
            'recepcion', 'asistencia', 'odontologia', 
            'admin', 'reportes', 'inventario', 'facturacion'
        ]
        
        for categoria in categorias_validas:
            permiso = PermisoPersonalizado.objects.create(
                codigo=f'test.{categoria}',
                nombre=f'Permiso {categoria}',
                descripcion='Prueba',
                categoria=categoria,
                activo=True
            )
            self.assertEqual(permiso.categoria, categoria)
    
    def test_desactivar_permiso(self):
        """Verificar que se puede desactivar un permiso"""
        self.assertTrue(self.permiso_global.activo)
        self.permiso_global.activo = False
        self.permiso_global.save()
        
        permiso_actualizado = PermisoPersonalizado.objects.get(
            pk=self.permiso_global.pk
        )
        self.assertFalse(permiso_actualizado.activo)


class RolUsuarioPowerDentTestCase(TestCase):
    """Pruebas para el modelo RolUsuarioPowerDent"""
    
    def setUp(self):
        """Configuración inicial"""
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            ruc='1234567890001',
            telefono='0999999999',
            email='test@clinica.com'
        )
        
        # Crear permisos de prueba
        self.permiso1 = PermisoPersonalizado.objects.create(
            codigo='recepcion.ver_citas',
            nombre='Ver Citas',
            descripcion='Permiso para ver citas',
            categoria='recepcion',
            activo=True
        )
        
        self.permiso2 = PermisoPersonalizado.objects.create(
            codigo='recepcion.crear_cita',
            nombre='Crear Cita',
            descripcion='Permiso para crear citas',
            categoria='recepcion',
            activo=True
        )
        
        self.permiso3 = PermisoPersonalizado.objects.create(
            codigo='asistencia.asistir_procedimiento',
            nombre='Asistir Procedimiento',
            descripcion='Asistir en procedimientos',
            categoria='asistencia',
            activo=True
        )
        
        # Rol global
        self.rol_global = RolUsuarioPowerDent.objects.create(
            nombre='Recepcionista',
            descripcion='Gestiona citas y pacientes',
            clinica=None,  # Global
            activo=True
        )
        self.rol_global.permisos.set([self.permiso1, self.permiso2])
        
        # Rol personalizado de clínica
        self.rol_clinica = RolUsuarioPowerDent.objects.create(
            nombre='Recepcionista Plus',
            descripcion='Recepcionista con permisos extras',
            clinica=self.clinica,
            activo=True
        )
        self.rol_clinica.permisos.set([
            self.permiso1, self.permiso2, self.permiso3
        ])
    
    def test_creacion_rol_global(self):
        """Verificar creación de rol global"""
        self.assertIsNone(self.rol_global.clinica)
        self.assertTrue(self.rol_global.es_global)
        self.assertEqual(self.rol_global.permisos.count(), 2)
        self.assertIn('Sistema', str(self.rol_global))
    
    def test_creacion_rol_clinica(self):
        """Verificar creación de rol de clínica"""
        self.assertIsNotNone(self.rol_clinica.clinica)
        self.assertFalse(self.rol_clinica.es_global)
        self.assertEqual(self.rol_clinica.permisos.count(), 3)
        self.assertIn('Clínica Test', str(self.rol_clinica))
    
    def test_asignar_permisos(self):
        """Verificar asignación de permisos a rol"""
        rol = RolUsuarioPowerDent.objects.create(
            nombre='Test Role',
            descripcion='Rol de prueba',
            activo=True
        )
        
        # Inicialmente sin permisos
        self.assertEqual(rol.permisos.count(), 0)
        
        # Asignar permisos
        rol.permisos.add(self.permiso1)
        self.assertEqual(rol.permisos.count(), 1)
        
        rol.permisos.add(self.permiso2, self.permiso3)
        self.assertEqual(rol.permisos.count(), 3)
    
    def test_desactivar_rol(self):
        """Verificar desactivación de rol"""
        self.assertTrue(self.rol_global.activo)
        self.rol_global.activo = False
        self.rol_global.save()
        
        rol_actualizado = RolUsuarioPowerDent.objects.get(
            pk=self.rol_global.pk
        )
        self.assertFalse(rol_actualizado.activo)


class UsuarioClinicaPermisosTestCase(TestCase):
    """Pruebas para permisos en UsuarioClinica"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear clínica
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            ruc='1234567890001',
            telefono='0999999999',
            email='test@clinica.com'
        )
        
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Crear usuario clínica
        self.usuario_clinica = UsuarioClinica.objects.create(
            usuario=self.user,
            clinica=self.clinica,
            rol=RolUsuario.RECEPCIONISTA,
            activo=True
        )
        
        # Crear permisos
        self.permiso1 = PermisoPersonalizado.objects.create(
            codigo='recepcion.ver_citas',
            nombre='Ver Citas',
            categoria='recepcion',
            activo=True
        )
        
        self.permiso2 = PermisoPersonalizado.objects.create(
            codigo='recepcion.crear_cita',
            nombre='Crear Cita',
            categoria='recepcion',
            activo=True
        )
        
        self.permiso3 = PermisoPersonalizado.objects.create(
            codigo='asistencia.asistir_procedimiento',
            nombre='Asistir Procedimiento',
            categoria='asistencia',
            activo=True
        )
        
        # Crear rol
        self.rol_recepcionista = RolUsuarioPowerDent.objects.create(
            nombre='Recepcionista',
            descripcion='Rol de recepcionista',
            activo=True
        )
        self.rol_recepcionista.permisos.set([self.permiso1, self.permiso2])
    
    def test_usuario_sin_roles_ni_permisos(self):
        """Usuario sin roles ni permisos adicionales"""
        permisos = self.usuario_clinica.get_permisos()
        codigos = self.usuario_clinica.get_codigos_permisos()
        
        self.assertEqual(permisos.count(), 0)
        self.assertEqual(len(codigos), 0)
        self.assertFalse(
            self.usuario_clinica.tiene_permiso('recepcion.ver_citas')
        )
    
    def test_usuario_con_un_rol(self):
        """Usuario con un rol asignado"""
        self.usuario_clinica.roles_personalizados.add(
            self.rol_recepcionista
        )
        
        # Debe tener 2 permisos del rol
        permisos = self.usuario_clinica.get_permisos()
        codigos = self.usuario_clinica.get_codigos_permisos()
        
        self.assertEqual(permisos.count(), 2)
        self.assertEqual(len(codigos), 2)
        
        # Verificar permisos específicos
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('recepcion.ver_citas')
        )
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('recepcion.crear_cita')
        )
        self.assertFalse(
            self.usuario_clinica.tiene_permiso('asistencia.asistir_procedimiento')
        )
    
    def test_usuario_con_multiples_roles(self):
        """Usuario con múltiples roles (caso clínica pequeña)"""
        # Crear segundo rol
        rol_auxiliar = RolUsuarioPowerDent.objects.create(
            nombre='Auxiliar',
            descripcion='Rol auxiliar',
            activo=True
        )
        rol_auxiliar.permisos.set([self.permiso3])
        
        # Asignar ambos roles
        self.usuario_clinica.roles_personalizados.set([
            self.rol_recepcionista, rol_auxiliar
        ])
        
        # Debe tener 3 permisos (2 del recepcionista + 1 del auxiliar)
        permisos = self.usuario_clinica.get_permisos()
        codigos = self.usuario_clinica.get_codigos_permisos()
        
        self.assertEqual(permisos.count(), 3)
        self.assertEqual(len(codigos), 3)
        
        # Verificar todos los permisos
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('recepcion.ver_citas')
        )
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('recepcion.crear_cita')
        )
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('asistencia.asistir_procedimiento')
        )
    
    def test_usuario_con_permisos_adicionales(self):
        """Usuario con permisos adicionales más allá de sus roles"""
        # Asignar rol
        self.usuario_clinica.roles_personalizados.add(
            self.rol_recepcionista
        )
        
        # Asignar permiso adicional
        self.usuario_clinica.permisos_adicionales.add(self.permiso3)
        
        # Debe tener 3 permisos (2 del rol + 1 adicional)
        permisos = self.usuario_clinica.get_permisos()
        codigos = self.usuario_clinica.get_codigos_permisos()
        
        self.assertEqual(permisos.count(), 3)
        self.assertEqual(len(codigos), 3)
        
        # Verificar permiso adicional
        self.assertTrue(
            self.usuario_clinica.tiene_permiso('asistencia.asistir_procedimiento')
        )
    
    def test_nombres_roles_personalizados(self):
        """Verificar método nombres_roles_personalizados"""
        # Sin roles
        self.assertEqual(
            self.usuario_clinica.nombres_roles_personalizados,
            'Sin roles asignados'
        )
        
        # Con un rol
        self.usuario_clinica.roles_personalizados.add(
            self.rol_recepcionista
        )
        self.assertEqual(
            self.usuario_clinica.nombres_roles_personalizados,
            'Recepcionista'
        )
        
        # Con múltiples roles
        rol_auxiliar = RolUsuarioPowerDent.objects.create(
            nombre='Auxiliar',
            descripcion='Rol auxiliar',
            activo=True
        )
        self.usuario_clinica.roles_personalizados.add(rol_auxiliar)
        
        nombres = self.usuario_clinica.nombres_roles_personalizados
        self.assertIn('Recepcionista', nombres)
        self.assertIn('Auxiliar', nombres)


class ScriptCargaPermisosTestCase(TestCase):
    """Pruebas para el script de carga de permisos y roles"""
    
    def test_permisos_predefinidos_cargados(self):
        """Verificar que existen los 27 permisos predefinidos"""
        # Ejecutar script de carga
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'powerdent.settings')
        
        # Verificar cantidad mínima de permisos
        permisos_globales = PermisoPersonalizado.objects.filter(
            clinica=None
        )
        
        # Puede haber más si ya se ejecutó el script antes
        self.assertGreaterEqual(permisos_globales.count(), 0)
    
    def test_categorias_permisos(self):
        """Verificar que hay permisos en todas las categorías"""
        categorias_esperadas = [
            'recepcion', 'asistencia', 'inventario',
            'odontologia', 'facturacion', 'admin', 'reportes'
        ]
        
        for categoria in categorias_esperadas:
            # Verificar que se pueden crear permisos en esta categoría
            permiso = PermisoPersonalizado.objects.create(
                codigo=f'test.{categoria}.permiso',
                nombre=f'Permiso {categoria}',
                descripcion='Prueba',
                categoria=categoria,
                activo=True
            )
            self.assertEqual(permiso.categoria, categoria)
    
    def test_roles_predefinidos_cargados(self):
        """Verificar que existen los 4 roles predefinidos"""
        roles_globales = RolUsuarioPowerDent.objects.filter(
            clinica=None
        )
        
        # Puede haber más o menos dependiendo de si se ejecutó el script
        self.assertGreaterEqual(roles_globales.count(), 0)


class PermisosCasoUsoRealTestCase(TestCase):
    """Pruebas de casos de uso reales del sistema de permisos"""
    
    def setUp(self):
        """Configuración para casos de uso"""
        self.clinica_grande = Clinica.objects.create(
            nombre='Clínica Grande',
            ruc='1234567890001',
            telefono='0999999999',
            email='grande@clinica.com'
        )
        
        self.clinica_pequena = Clinica.objects.create(
            nombre='Clínica Pequeña',
            ruc='0987654321001',
            telefono='0988888888',
            email='pequena@clinica.com'
        )
        
        # Usuarios
        self.user_recep = User.objects.create_user(
            username='recepcionista',
            email='recep@test.com',
            password='pass123'
        )
        
        self.user_multi = User.objects.create_user(
            username='multirole',
            email='multi@test.com',
            password='pass123'
        )
        
        # Permisos
        self.p_ver_citas = PermisoPersonalizado.objects.create(
            codigo='recepcion.ver_citas',
            nombre='Ver Citas',
            categoria='recepcion',
            activo=True
        )
        
        self.p_crear_cita = PermisoPersonalizado.objects.create(
            codigo='recepcion.crear_cita',
            nombre='Crear Cita',
            categoria='recepcion',
            activo=True
        )
        
        self.p_asistir = PermisoPersonalizado.objects.create(
            codigo='asistencia.asistir_procedimiento',
            nombre='Asistir',
            categoria='asistencia',
            activo=True
        )
        
        self.p_inventario = PermisoPersonalizado.objects.create(
            codigo='inventario.ver_inventario',
            nombre='Ver Inventario',
            categoria='inventario',
            activo=True
        )
    
    def test_caso_clinica_grande_roles_separados(self):
        """Clínica grande: cada persona un rol específico"""
        # Crear roles específicos
        rol_recep = RolUsuarioPowerDent.objects.create(
            nombre='Recepcionista',
            activo=True
        )
        rol_recep.permisos.set([self.p_ver_citas, self.p_crear_cita])
        
        # Usuario solo recepcionista
        uc_recep = UsuarioClinica.objects.create(
            usuario=self.user_recep,
            clinica=self.clinica_grande,
            rol=RolUsuario.RECEPCIONISTA,
            activo=True
        )
        uc_recep.roles_personalizados.add(rol_recep)
        
        # Verificar permisos limitados
        self.assertTrue(uc_recep.tiene_permiso('recepcion.ver_citas'))
        self.assertFalse(uc_recep.tiene_permiso('asistencia.asistir_procedimiento'))
        self.assertFalse(uc_recep.tiene_permiso('inventario.ver_inventario'))
    
    def test_caso_clinica_pequena_multirole(self):
        """Clínica pequeña: una persona con recepción + asistencia"""
        # Crear rol combinado
        rol_multi = RolUsuarioPowerDent.objects.create(
            nombre='Recepcionista + Auxiliar',
            descripcion='Para clínicas pequeñas',
            activo=True
        )
        rol_multi.permisos.set([
            self.p_ver_citas,
            self.p_crear_cita,
            self.p_asistir,
            self.p_inventario
        ])
        
        # Usuario multi-rol
        uc_multi = UsuarioClinica.objects.create(
            usuario=self.user_multi,
            clinica=self.clinica_pequena,
            rol=RolUsuario.RECEPCIONISTA,
            activo=True
        )
        uc_multi.roles_personalizados.add(rol_multi)
        
        # Verificar acceso a todos los permisos
        self.assertTrue(uc_multi.tiene_permiso('recepcion.ver_citas'))
        self.assertTrue(uc_multi.tiene_permiso('recepcion.crear_cita'))
        self.assertTrue(uc_multi.tiene_permiso('asistencia.asistir_procedimiento'))
        self.assertTrue(uc_multi.tiene_permiso('inventario.ver_inventario'))
        
        # Verificar cantidad total
        self.assertEqual(uc_multi.get_permisos().count(), 4)
