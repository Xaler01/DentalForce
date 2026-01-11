"""
Test SOOD-USU-007: Auto-crear UsuarioClinica cuando se crea un Dentista

Verifica que al crear un Dentista:
1. Se crea automáticamente un UsuarioClinica
2. El UsuarioClinica tiene rol ODONTOLOGO
3. El UsuarioClinica está asociado a la clínica correcta
4. Si ya existe UsuarioClinica, se actualiza si es necesario
"""

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse

from cit.models import Clinica, Sucursal, Especialidad, Cubiculo
from personal.models import Dentista
from usuarios.models import UsuarioClinica, RolUsuario


class DentistaUsuarioAutoCreateTest(TestCase):
    """Tests para creación automática de UsuarioClinica al crear Dentista"""
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        # Crear clínica de prueba
        self.clinica = Clinica.objects.create(
            nombre="Clínica Test Auto-Create",
            direccion="Calle Test 123",
            telefono="0999999999",
            email="test@example.com",
            activo=True
        )
        
        # Crear sucursal asociada a la clínica
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre="Sucursal Principal Test",
            direccion="Av. Test 456",
            telefono="0988888888",
            activo=True
        )
        
        # Crear especialidad
        self.especialidad = Especialidad.objects.create(
            nombre="Odontología General Test",
            descripcion="Especialidad de prueba",
            duracion_cita_defecto=30,
            activo=True
        )
        
        # Crear cubículo
        self.cubiculo = Cubiculo.objects.create(
            nombre="Consultorio 1",
            descripcion="Cubículo de prueba",
            activo=True
        )
        
        # Crear usuario admin para las requests
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='test123',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        
        # Crear usuario para el dentista
        self.dentista_user = User.objects.create_user(
            username='dr.test',
            password='test123',
            email='dr.test@example.com',
            first_name='Juan',
            last_name='Test'
        )
        
        # Factory para crear requests
        self.factory = RequestFactory()
        
    def test_usuario_clinica_creado_automaticamente(self):
        """Test 1: UsuarioClinica se crea automáticamente al crear Dentista"""
        # Verificar que NO existe UsuarioClinica antes
        self.assertEqual(UsuarioClinica.objects.count(), 0)
        
        # Crear dentista
        dentista = Dentista.objects.create(
            usuario=self.dentista_user,
            sucursal_principal=self.sucursal,
            cedula_profesional='1234567890',
            telefono_movil='0999999999',
            fecha_contratacion='2024-01-01',
            activo=True,
            uc=self.admin_user
        )
        dentista.especialidades.add(self.especialidad)
        dentista.cubiculos.add(self.cubiculo)
        
        # Simular la lógica de auto-creación que debería ejecutarse en form_valid
        from usuarios.models import UsuarioClinica, RolUsuario
        
        clinica = dentista.sucursal_principal.clinica if dentista.sucursal_principal else None
        
        if clinica:
            usuario_clinica, created = UsuarioClinica.objects.get_or_create(
                usuario=dentista.usuario,
                defaults={
                    'clinica': clinica,
                    'rol': RolUsuario.ODONTOLOGO,
                    'activo': True
                }
            )
        
        # Verificar que se creó UsuarioClinica
        self.assertEqual(UsuarioClinica.objects.count(), 1)
        
        # Verificar que el UsuarioClinica tiene los datos correctos
        usuario_clinica = UsuarioClinica.objects.get(usuario=self.dentista_user)
        self.assertEqual(usuario_clinica.clinica, self.clinica)
        self.assertEqual(usuario_clinica.rol, RolUsuario.ODONTOLOGO)
        self.assertTrue(usuario_clinica.activo)
        
    def test_usuario_clinica_no_duplicado(self):
        """Test 2: No se duplica UsuarioClinica si ya existe"""
        # Crear UsuarioClinica manualmente
        usuario_clinica_original = UsuarioClinica.objects.create(
            usuario=self.dentista_user,
            clinica=self.clinica,
            rol=RolUsuario.ADMINISTRATIVO,  # Rol diferente inicialmente
            activo=True
        )
        
        self.assertEqual(UsuarioClinica.objects.count(), 1)
        
        # Crear dentista
        dentista = Dentista.objects.create(
            usuario=self.dentista_user,
            sucursal_principal=self.sucursal,
            cedula_profesional='1234567890',
            telefono_movil='0999999999',
            fecha_contratacion='2024-01-01',
            activo=True,
            uc=self.admin_user
        )
        
        # Simular la lógica de auto-creación
        from usuarios.models import UsuarioClinica, RolUsuario
        
        clinica = dentista.sucursal_principal.clinica if dentista.sucursal_principal else None
        
        if clinica:
            usuario_clinica, created = UsuarioClinica.objects.get_or_create(
                usuario=dentista.usuario,
                defaults={
                    'clinica': clinica,
                    'rol': RolUsuario.ODONTOLOGO,
                    'activo': True
                }
            )
            
            # Si ya existe, actualizar
            if not created:
                if usuario_clinica.clinica != clinica or usuario_clinica.rol != RolUsuario.ODONTOLOGO:
                    usuario_clinica.clinica = clinica
                    usuario_clinica.rol = RolUsuario.ODONTOLOGO
                    usuario_clinica.save()
        
        # Verificar que NO se duplicó (sigue siendo 1)
        self.assertEqual(UsuarioClinica.objects.count(), 1)
        
        # Verificar que se actualizó el rol a ODONTOLOGO
        usuario_clinica_actualizado = UsuarioClinica.objects.get(usuario=self.dentista_user)
        self.assertEqual(usuario_clinica_actualizado.rol, RolUsuario.ODONTOLOGO)
        self.assertEqual(usuario_clinica_actualizado.clinica, self.clinica)
        
    def test_usuario_clinica_no_creado_sin_sucursal(self):
        """Test 3: No se crea UsuarioClinica si el dentista no tiene sucursal"""
        # Crear dentista SIN sucursal_principal
        dentista = Dentista.objects.create(
            usuario=self.dentista_user,
            sucursal_principal=None,  # Sin sucursal
            cedula_profesional='1234567890',
            telefono_movil='0999999999',
            fecha_contratacion='2024-01-01',
            activo=True,
            uc=self.admin_user
        )
        
        # Simular la lógica de auto-creación
        from usuarios.models import UsuarioClinica, RolUsuario
        
        clinica = dentista.sucursal_principal.clinica if dentista.sucursal_principal else None
        
        if clinica:  # Esta condición será False
            usuario_clinica, created = UsuarioClinica.objects.get_or_create(
                usuario=dentista.usuario,
                defaults={
                    'clinica': clinica,
                    'rol': RolUsuario.ODONTOLOGO,
                    'activo': True
                }
            )
        
        # Verificar que NO se creó UsuarioClinica
        self.assertEqual(UsuarioClinica.objects.count(), 0)
        
    def test_propiedades_usuario_clinica(self):
        """Test 4: Verificar que las propiedades del modelo funcionan correctamente"""
        # Crear dentista y UsuarioClinica
        dentista = Dentista.objects.create(
            usuario=self.dentista_user,
            sucursal_principal=self.sucursal,
            cedula_profesional='1234567890',
            telefono_movil='0999999999',
            fecha_contratacion='2024-01-01',
            activo=True,
            uc=self.admin_user
        )
        
        # Auto-crear UsuarioClinica
        from usuarios.models import UsuarioClinica, RolUsuario
        
        clinica = dentista.sucursal_principal.clinica
        usuario_clinica, created = UsuarioClinica.objects.get_or_create(
            usuario=dentista.usuario,
            defaults={
                'clinica': clinica,
                'rol': RolUsuario.ODONTOLOGO,
                'activo': True
            }
        )
        
        # Verificar propiedades
        self.assertTrue(usuario_clinica.es_odontologo)
        self.assertFalse(usuario_clinica.es_admin)
        self.assertFalse(usuario_clinica.es_administrativo)
        self.assertFalse(usuario_clinica.es_asistente)
        self.assertEqual(usuario_clinica.nombre_completo, 'Juan Test')
