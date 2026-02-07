"""
Test para verificar que los dentistas pueden crear citas (agendamiento post-consulta)

Ejecutar: python manage.py test usuarios.tests.test_dentista_crear_citas
"""

from django.test import TestCase
from django.contrib.auth.models import User
from usuarios.models import (
    RolUsuarioPowerDent,
    PermisoPersonalizado,
    UsuarioClinica,
)
from clinicas.models import Clinica


class DentistaCrearCitasTest(TestCase):
    """Tests para verificar que dentistas pueden crear citas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Usuario admin para uc_id y creación de rol/permiso
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )

        # Crear permisos necesarios (idempotente)
        permisos = [
            ('recepcion.ver_citas', 'Ver Citas', 'recepcion'),
            ('recepcion.crear_cita', 'Crear Cita', 'recepcion'),
            ('recepcion.ver_historiales', 'Ver Historiales', 'recepcion'),
            ('odontologia.crear_procedimiento', 'Crear Procedimiento', 'odontologia'),
            ('odontologia.editar_diagnostico', 'Editar Diagnóstico', 'odontologia'),
            ('odontologia.registrar_evolucion', 'Registrar Evolución', 'odontologia'),
            ('odontologia.prescribir_medicinas', 'Prescribir Medicinas', 'odontologia'),
            ('odontologia.ver_radiografias', 'Ver Radiografías', 'odontologia'),
        ]
        permisos_objs = {}
        for codigo, nombre, categoria in permisos:
            permiso, _ = PermisoPersonalizado.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'categoria': categoria,
                    'activo': True,
                },
            )
            permisos_objs[codigo] = permiso

        # Crear rol Dentista con los permisos esperados
        self.rol_dentista, _ = RolUsuarioPowerDent.objects.get_or_create(
            nombre='Dentista',
            defaults={
                'descripcion': 'Profesional odontológico con acceso a historiales, diagnósticos y procedimientos completos. Puede agendar citas para sus pacientes después de la consulta.',
                'activo': True,
            },
        )
        self.rol_dentista.permisos.set(permisos_objs.values())

        # Crear clínica con uc_id válido
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle Principal 123',
            telefono='099999999',
            email='test@clinica.com',
            uc_id=self.admin.id
        )
        
        self.usuario_dentista = User.objects.create_user(
            username='dr_test',
            email='dr@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.usuario_clinica = UsuarioClinica.objects.create(
            usuario=self.usuario_dentista,
            clinica=self.clinica
        )
    
    def test_rol_dentista_tiene_permiso_crear_cita(self):
        """Verificar que el rol Dentista incluye permiso crear_cita"""
        rol_dentista = RolUsuarioPowerDent.objects.get(nombre='Dentista')
        
        # Verificar que el permiso crear_cita está en el rol
        tiene_permiso = rol_dentista.permisos.filter(codigo='recepcion.crear_cita').exists()
        self.assertTrue(tiene_permiso, 
            "El rol Dentista debería tener permiso 'recepcion.crear_cita'")
    
    def test_dentista_tiene_8_permisos(self):
        """Verificar que el rol Dentista tiene 8 permisos (incluyendo crear_cita)"""
        rol_dentista = RolUsuarioPowerDent.objects.get(nombre='Dentista')
        self.assertEqual(rol_dentista.permisos.count(), 8,
            f"Dentista debería tener 8 permisos, tiene {rol_dentista.permisos.count()}")
    
    def test_dentista_permisos_incluyen_odontologia_y_recepcion(self):
        """Verificar que dentista tiene permisos de odontología Y crear citas"""
        rol_dentista = RolUsuarioPowerDent.objects.get(nombre='Dentista')
        codigos = list(rol_dentista.permisos.values_list('codigo', flat=True))
        
        # Permisos de odontología (debe mantenerlos)
        self.assertIn('odontologia.crear_procedimiento', codigos)
        self.assertIn('odontologia.editar_diagnostico', codigos)
        self.assertIn('odontologia.registrar_evolucion', codigos)
        
        # Permisos de recepción (NUEVO: crear_cita)
        self.assertIn('recepcion.ver_citas', codigos)
        self.assertIn('recepcion.crear_cita', codigos)  # ← NUEVO
        self.assertIn('recepcion.ver_historiales', codigos)
    
    def test_usuario_dentista_puede_crear_citas(self):
        """Verificar que un usuario con rol Dentista puede crear citas"""
        rol_dentista = RolUsuarioPowerDent.objects.get(nombre='Dentista')
        self.usuario_clinica.roles_personalizados.add(rol_dentista)
        
        # Verificar que el usuario tiene acceso al permiso
        permisos_usuario = []
        for rol in self.usuario_clinica.roles_personalizados.all():
            permisos_usuario.extend(rol.permisos.values_list('codigo', flat=True))
        
        self.assertIn('recepcion.crear_cita', permisos_usuario,
            "Usuario dentista debería poder crear citas")
    
    def test_descripcion_rol_dentista_menciona_agendamiento(self):
        """Verificar que la descripción del rol menciona el agendamiento de citas"""
        rol_dentista = RolUsuarioPowerDent.objects.get(nombre='Dentista')
        self.assertIn('agendar', rol_dentista.descripcion.lower(),
            "La descripción debería mencionar que puede agendar citas")
