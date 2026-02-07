"""
Tests para verificar que el rol "Odontólogo Director" está correctamente configurado
con todos los permisos necesarios incluyendo facturación.

Ejecutar: python manage.py test usuarios.tests.test_odontolog_director
"""

from django.test import TestCase
from usuarios.models import RolUsuarioDentalForce, PermisoPersonalizado, UsuarioClinica
from clinicas.models import Clinica
from django.contrib.auth.models import User


class OdontologDirectorRoleTest(TestCase):
    """Tests para el rol Odontólogo Director"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear clínica de prueba
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle Principal 123',
            telefono='099999999',
            email='test@clinica.com',
            uc_id=1  # Admin que crea
        )
        
        # Crear usuario
        self.usuario = User.objects.create_user(
            username='dr_test',
            email='dr@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Crear asignación usuario-clínica
        self.usuario_clinica = UsuarioClinica.objects.create(
            usuario=self.usuario,
            clinica=self.clinica
        )
    
    def test_rol_odontolog_director_existe(self):
        """Verificar que el rol Odontólogo Director existe"""
        rol = RolUsuarioDentalForce.objects.filter(nombre='Odontólogo Director').first()
        self.assertIsNotNone(rol, "Rol 'Odontólogo Director' no existe")
    
    def test_rol_tiene_19_permisos(self):
        """Verificar que el rol tiene exactamente 19 permisos"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        self.assertEqual(rol.permisos.count(), 19, 
            f"Rol debería tener 19 permisos, tiene {rol.permisos.count()}")
    
    def test_rol_tiene_permisos_odontologia(self):
        """Verificar que el rol incluye todos los permisos de odontología"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        codigos_esperados = [
            'odontologia.crear_procedimiento',
            'odontologia.editar_diagnostico',
            'odontologia.registrar_evolucion',
            'odontologia.prescribir_medicinas',
            'odontologia.ver_radiografias',
        ]
        
        codigos_actuales = list(rol.permisos.values_list('codigo', flat=True))
        
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_actuales, 
                f"Permiso '{codigo}' falta en el rol Odontólogo Director")
    
    def test_rol_tiene_permisos_recepcion(self):
        """Verificar que el rol incluye todos los permisos de recepción"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        codigos_esperados = [
            'recepcion.ver_citas',
            'recepcion.crear_cita',
            'recepcion.editar_cita',
            'recepcion.cancelar_cita',
            'recepcion.gestionar_pacientes',
            'recepcion.ver_historiales',
        ]
        
        codigos_actuales = list(rol.permisos.values_list('codigo', flat=True))
        
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_actuales,
                f"Permiso '{codigo}' falta en el rol Odontólogo Director")
    
    def test_rol_tiene_permisos_facturacion_completos(self):
        """✅ Verificar que el rol incluye TODOS los permisos de facturación"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        codigos_esperados = [
            'facturacion.ver_facturas',
            'facturacion.crear_factura',
            'facturacion.editar_factura',
            'facturacion.anular_factura',
        ]
        
        codigos_actuales = list(rol.permisos.values_list('codigo', flat=True))
        
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_actuales,
                f"⚠️ Permiso de facturación '{codigo}' falta en el rol Odontólogo Director")
    
    def test_rol_tiene_permisos_inventario(self):
        """Verificar que el rol incluye permisos de inventario básico"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        codigos_esperados = [
            'inventario.ver_inventario',
            'inventario.solicitar_inventario',
        ]
        
        codigos_actuales = list(rol.permisos.values_list('codigo', flat=True))
        
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_actuales,
                f"Permiso '{codigo}' falta en el rol Odontólogo Director")
    
    def test_rol_tiene_permisos_reportes(self):
        """Verificar que el rol incluye permisos de reportes básicos"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        codigos_esperados = [
            'reportes.ver_reportes_general',
            'reportes.ver_reportes_financiero',
        ]
        
        codigos_actuales = list(rol.permisos.values_list('codigo', flat=True))
        
        for codigo in codigos_esperados:
            self.assertIn(codigo, codigos_actuales,
                f"Permiso '{codigo}' falta en el rol Odontólogo Director")
    
    def test_rol_es_global_no_por_clinica(self):
        """Verificar que el rol Odontólogo Director es global (no específico de clínica)"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        self.assertIsNone(rol.clinica, 
            "Rol Odontólogo Director debería ser global (clinica=None)")
    
    def test_rol_esta_activo(self):
        """Verificar que el rol está activo"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        self.assertTrue(rol.activo, "Rol Odontólogo Director debería estar activo")
    
    def test_asignar_rol_a_usuario(self):
        """Verificar que podemos asignar el rol a un usuario"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        self.usuario_clinica.roles_personalizados.add(rol)
        
        self.assertIn(rol, self.usuario_clinica.roles_personalizados.all(),
            "No se pudo asignar el rol al usuario")
    
    def test_usuario_con_rol_tiene_acceso_a_facturacion(self):
        """Verificar que un usuario con el rol puede acceder a facturación"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        self.usuario_clinica.roles_personalizados.add(rol)
        
        # Obtener los permisos del usuario a través del rol
        permisos_codigos = []
        for r in self.usuario_clinica.roles_personalizados.all():
            permisos_codigos.extend(r.permisos.values_list('codigo', flat=True))
        
        # Verificar permisos de facturación
        self.assertIn('facturacion.ver_facturas', permisos_codigos)
        self.assertIn('facturacion.crear_factura', permisos_codigos)
        self.assertIn('facturacion.editar_factura', permisos_codigos)
        self.assertIn('facturacion.anular_factura', permisos_codigos)
    
    def test_rol_resumen(self):
        """Mostrar un resumen completo del rol (para debugging)"""
        rol = RolUsuarioDentalForce.objects.get(nombre='Odontólogo Director')
        permisos = rol.permisos.all().order_by('categoria', 'nombre')
        
        print("\n" + "="*60)
        print(f"ROL: {rol.nombre}")
        print(f"Descripción: {rol.descripcion}")
        print(f"Total Permisos: {permisos.count()}")
        print("="*60)
        
        categorias = {}
        for p in permisos:
            if p.categoria not in categorias:
                categorias[p.categoria] = []
            categorias[p.categoria].append(p)
        
        for categoria in sorted(categorias.keys()):
            print(f"\n{categoria.upper()} ({len(categorias[categoria])}):")
            for p in categorias[categoria]:
                print(f"  ✓ {p.nombre}")
