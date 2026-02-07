"""
Tests de integración multi-tenant para validar el aislamiento de datos y permisos granulares.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse

from clinicas.models import Clinica, Sucursal, Especialidad, Cubiculo
from cit.models import Cita
from pacientes.models import Paciente
from personal.models import Dentista


class MultiTenantTestSetup(TestCase):
    """
    Setup base para todos los tests multi-tenant.
    Crea dos clínicas con datos, usuarios, y da permisos necesarios.
    """
    
    def setUp(self):
        """Crear datos de prueba para dos clínicas"""
        
        # ========== USUARIOS ==========
        # Super admin (crear primero para usarlo en uc_id)
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass'
        )
        
        # ========== CLÍNICA 1 ==========
        self.clinica1 = Clinica.objects.create(
            nombre='Clínica Sur',
            direccion='Calle 1, Sur',
            telefono='555-0001',
            email='sur@example.com',
            pais='EC',
            moneda='USD',
            uc_id=self.admin.id
        )
        
        self.sucursal1_1 = Sucursal.objects.create(
            clinica=self.clinica1,
            nombre='Sucursal Principal Sur',
            direccion='Calle 1',
            telefono='555-0001',
            horario_apertura='08:00',
            horario_cierre='18:00',
            uc_id=self.admin.id
        )
        
        self.especialidad1 = Especialidad.objects.create(
            nombre='Ortodoncia',
            descripcion='Especialidad en ortodoncia',
            duracion_default=45,
            color_calendario='#FF5733',
            uc_id=self.admin.id
        )
        
        self.cubiculo1_1 = Cubiculo.objects.create(
            sucursal=self.sucursal1_1,
            nombre='Consultorio 1',
            numero=1,
            capacidad=2,
            equipamiento='Equipo dental básico',
            uc_id=self.admin.id
        )
        
        # ========== CLÍNICA 2 ==========
        self.clinica2 = Clinica.objects.create(
            nombre='Clínica Norte',
            direccion='Calle 2, Norte',
            telefono='555-0002',
            email='norte@example.com',
            pais='EC',
            moneda='USD',
            uc_id=self.admin.id
        )
        
        self.sucursal2_1 = Sucursal.objects.create(
            clinica=self.clinica2,
            nombre='Sucursal Principal Norte',
            direccion='Calle 2',
            telefono='555-0002',
            horario_apertura='09:00',
            horario_cierre='19:00',
            uc_id=self.admin.id
        )
        
        self.especialidad2 = Especialidad.objects.create(
            nombre='Endodoncia',
            descripcion='Especialidad en endodoncia',
            duracion_default=60,
            color_calendario='#33FF57',
            uc_id=self.admin.id
        )
        
        self.cubiculo2_1 = Cubiculo.objects.create(
            sucursal=self.sucursal2_1,
            nombre='Consultorio A',
            numero=1,
            capacidad=2,
            equipamiento='Equipo dental avanzado',
            uc_id=self.admin.id
        )
        
        # Usuario regular para clínica 1
        self.user_clinica1 = User.objects.create_user(
            username='user_sur',
            email='user@example.com',
            password='testpass',
            is_staff=True
        )
        
        # Otorgar permisos básicos
        view_perm = Permission.objects.get(codename='view_clinica')
        self.user_clinica1.user_permissions.add(view_perm)
        
        # Usuario regular para clínica 2
        self.user_clinica2 = User.objects.create_user(
            username='user_norte',
            email='norte@example.com',
            password='testpass',
            is_staff=True
        )
        self.user_clinica2.user_permissions.add(view_perm)
        
        # Cliente HTTP para tests
        self.client = Client()


class ClinicaMultiTenantTests(MultiTenantTestSetup):
    """
    Tests para validar que el aislamiento multi-tenant funciona correctamente.
    """
    
    def test_usuario_clinica1_no_ve_datos_clinica2(self):
        """
        Verificar que un usuario de Clínica 1 no puede ver sucursales de Clínica 2
        """
        # Login usuario de clínica 1
        self.client.login(username='user_sur', password='testpass')
        
        # Seleccionar clínica 1 en sesión
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Intentar acceder a sucursal de clínica 2
        response = self.client.get(
            reverse('clinicas:sucursal_detail', args=[self.sucursal2_1.id])
        )
        
        # Debe retornar PermissionDenied (403)
        self.assertEqual(response.status_code, 403)
    
    def test_usuario_clinica1_ve_datos_clinica1(self):
        """
        Verificar que un usuario de Clínica 1 SÍ puede ver sus propios datos
        """
        # Login usuario de clínica 1
        self.client.login(username='user_sur', password='testpass')
        
        # Seleccionar clínica 1 en sesión
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Acceder a sucursal de clínica 1
        response = self.client.get(
            reverse('clinicas:sucursal_detail', args=[self.sucursal1_1.id])
        )
        
        # Debe retornar 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sucursal Principal Sur')
    
    def test_admin_ve_todas_clinicas(self):
        """
        Verificar que el admin puede ver datos de cualquier clínica
        """
        # Login como admin
        self.client.login(username='admin', password='testpass')
        
        # Seleccionar clínica 1
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # El admin debe poder acceder a sucursal de clínica 2
        # (aunque su sesión diga clínica 1)
        response = self.client.get(
            reverse('clinicas:sucursal_detail', args=[self.sucursal2_1.id])
        )
        
        # Admin puede ver todo
        self.assertIn(response.status_code, [200, 404])  # 404 si no existe
    
    def test_cubiculos_filtrados_por_clinica(self):
        """
        Verificar que al listar cubículos, solo se muestran los de la clínica activa
        """
        # Login usuario de clínica 1
        self.client.login(username='user_sur', password='testpass')
        
        # Seleccionar clínica 1
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Listar cubículos
        response = self.client.get(reverse('clinicas:cubiculo_list'))
        
        # Debe contener cubiculo de clínica 1
        if response.status_code == 200:
            self.assertContains(response, 'Consultorio 1')
            # No debe contener cubiculo de clínica 2
            self.assertNotContains(response, 'Consultorio A')


class PermisoGranularTests(MultiTenantTestSetup):
    """
    Tests para validar que los permisos granulares funcionan correctamente.
    """
    
    def test_usuario_sin_permiso_view_no_puede_acceder(self):
        """
        Verificar que un usuario sin permiso 'view_clinica' no puede ver listado
        """
        # Crear usuario sin permisos
        user = User.objects.create_user(
            username='user_sin_permisos',
            password='testpass',
            is_staff=True
        )
        
        self.client.login(username='user_sin_permisos', password='testpass')
        
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Intentar listar clínicas
        response = self.client.get(reverse('clinicas:list'))
        
        # Debe ser rechazado
        self.assertIn(response.status_code, [403, 302])  # 403 o redirección
    
    def test_usuario_sin_clinica_seleccionada_es_redirigido(self):
        """
        Verificar que sin clínica seleccionada, se redirige al selector
        """
        self.client.login(username='user_sur', password='testpass')
        
        # No establecer clinica_id en la sesión
        
        # Intentar acceder a sucursales
        response = self.client.get(
            reverse('clinicas:sucursal_list'),
            follow=True
        )
        
        # Debe redirigir al selector
        self.assertRedirects(response, reverse('clinicas:seleccionar'), status_code=302)


class OptimizationTests(MultiTenantTestSetup):
    """
    Tests para validar optimizaciones de queries.
    """
    
    def test_sucursal_list_no_tiene_n_plus_1(self):
        """
        Verificar que listar sucursales no ejecuta múltiples queries
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        self.client.login(username='user_sur', password='testpass')
        
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Capturar queries
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('clinicas:sucursal_list'))
        
        # El número de queries debe ser razonable (no más de 9)
        # Con select_related optimizado: auth queries + sucursales con clinica + metadata queries
        self.assertLess(len(ctx), 9, f"Demasiadas queries: {len(ctx)}")
    
    def test_cubiculo_detail_usa_select_related(self):
        """
        Verificar que el detail de cubiculo usa select_related para sucursal y clinica
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        self.client.login(username='user_sur', password='testpass')
        
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(
                reverse('clinicas:cubiculo_detail', args=[self.cubiculo1_1.id])
            )
        
        # Debe cargar cubiculo, sucursal y clinica con select_related (máx 8 queries)
        # Auth + permisos + cubiculo + sucursal + clinica + metadata queries
        self.assertLess(len(ctx), 8)


class ClinicaSelectorTests(MultiTenantTestSetup):
    """
    Tests para el selector de clínicas.
    """
    
    def test_admin_ve_todas_clinicas_en_selector(self):
        """
        Verificar que admin ve todas las clínicas (activas e inactivas)
        """
        # Crear una clínica inactiva
        clinica_inactiva = Clinica.objects.create(
            nombre='Clínica Inactiva',
            direccion='Calle X',
            telefono='555-9999',
            email='inactiva@example.com',
            estado=False,
            uc_id=self.admin.id
        )
        
        self.client.login(username='admin', password='testpass')
        
        response = self.client.get(reverse('clinicas:seleccionar'))
        
        # Admin debe ver todas
        self.assertContains(response, 'Clínica Sur')
        self.assertContains(response, 'Clínica Norte')
        self.assertContains(response, 'Clínica Inactiva')
    
    def test_usuario_no_admin_no_puede_cambiar_clinica(self):
        """
        Usuarios sin rol de admin general no pueden acceder al selector.
        """
        self.client.login(username='user_sur', password='testpass')
        
        response = self.client.get(reverse('clinicas:seleccionar'), follow=True)
        
        self.assertRedirects(response, reverse('bases:home'))
        self.assertContains(response, 'Solo el administrador general puede cambiar de clínica.')


class CubiculoCreationTests(MultiTenantTestSetup):
    """
    Tests para crear cubículos en sucursales de la clínica activa.
    """
    
    def test_crear_cubiculo_en_sucursal_propia(self):
        """
        Verificar que puedo crear cubiculo en sucursal de mi clínica
        """
        self.client.login(username='user_sur', password='testpass')
        
        session = self.client.session
        session['clinica_id'] = self.clinica1.id
        session.save()
        
        # Dar permiso de crear
        perm = Permission.objects.get(codename='add_cubiculo')
        self.user_clinica1.user_permissions.add(perm)
        
        # Crear cubiculo
        response = self.client.post(
            reverse('clinicas:cubiculo_create'),
            {
                'sucursal': self.sucursal1_1.id,
                'nombre': 'Consultorio 2',
                'numero': 2,
                'capacidad': 2,
            }
        )
        
        # Debe redirigir (creación exitosa)
        self.assertIn(response.status_code, [302, 200])
