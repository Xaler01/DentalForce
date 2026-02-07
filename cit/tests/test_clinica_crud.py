"""
Tests para el CRUD de Clínicas
SOOD-47: CRUD de Clínicas - Implementar vistas y formularios
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from cit.models import Clinica, Sucursal
from cit.forms import ClinicaForm
from datetime import time
from cit.tests.base import MultiTenantTestCase


class ClinicaModelTest(TestCase):
    """Tests para el modelo Clinica"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        
    def test_crear_clinica(self):
        """Test: crear una clínica con datos básicos"""
        clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user
        )
        
        self.assertEqual(clinica.nombre, 'Clínica Test')
        self.assertEqual(clinica.telefono, '02-1234567')
        self.assertTrue(clinica.estado)  # Activa por defecto
        self.assertEqual(clinica.pais, 'EC')  # Ecuador por defecto
        self.assertEqual(clinica.moneda, 'USD')  # USD por defecto
    
    def test_crear_clinica_con_datos_fiscales(self):
        """Test: crear clínica con datos fiscales completos"""
        clinica = Clinica.objects.create(
            nombre='DentalForce S.A.',
            razon_social='DentalForce Sociedad Anónima',
            ruc='1234567890001',
            representante_legal='Juan Pérez',
            direccion='Av. Principal 100',
            telefono='02-9999999',
            email='info@dentalforce.com',
            pais='EC',
            moneda='USD',
            uc=self.user
        )
        
        self.assertEqual(clinica.ruc, '1234567890001')
        self.assertEqual(clinica.razon_social, 'DentalForce Sociedad Anónima')
        self.assertEqual(clinica.representante_legal, 'Juan Pérez')
    
    def test_get_nombre_completo(self):
        """Test: método get_nombre_completo retorna razón social si existe"""
        clinica = Clinica.objects.create(
            nombre='DentalForce',
            razon_social='DentalForce S.A.',
            direccion='Av. Test',
            telefono='02-1234567',
            email='test@test.com',
            uc=self.user
        )
        
        self.assertEqual(clinica.get_nombre_completo(), 'DentalForce S.A.')
    
    def test_clinica_str(self):
        """Test: representación en string de clínica"""
        clinica = Clinica.objects.create(
            nombre='DentalForce',
            direccion='Av. Principal',
            telefono='02-9999999',
            email='info@dentalforce.com',
            uc=self.user
        )
        
        self.assertEqual(str(clinica), 'DentalForce')


class ClinicaFormTest(TestCase):
    """Tests para el formulario de Clínica"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
    
    def test_formulario_valido_basico(self):
        """Test: formulario válido con datos básicos"""
        form_data = {
            'nombre': 'Clínica Nueva',
            'direccion': 'Calle Principal 456',
            'telefono': '02-7654321',
            'email': 'nueva@clinica.com',
            'pais': 'EC',
            'moneda': 'USD',
            'zona_horaria': 'America/Guayaquil'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_valido_con_datos_fiscales(self):
        """Test: formulario válido con datos fiscales completos"""
        form_data = {
            'nombre': 'DentalForce',
            'razon_social': 'DentalForce S.A.',
            'ruc': '1234567890001',
            'representante_legal': 'Juan Pérez',
            'direccion': 'Av. Principal 100',
            'telefono': '02-9999999',
            'email': 'info@dentalforce.com',
            'pais': 'EC',
            'moneda': 'USD',
            'zona_horaria': 'America/Guayaquil'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_validacion_ruc_ecuador(self):
        """Test: validación de RUC ecuatoriano (13 dígitos)"""
        form_data = {
            'nombre': 'Clínica EC',
            'direccion': 'Av. Test',
            'telefono': '02-1234567',
            'email': 'test@ec.com',
            'ruc': '123456789',  # Inválido: menos de 13 dígitos
            'pais': 'EC',
            'moneda': 'USD',
            'zona_horaria': 'America/Guayaquil'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ruc', form.errors)
    
    def test_validacion_ruc_peru(self):
        """Test: validación de RUC peruano (11 dígitos)"""
        form_data = {
            'nombre': 'Clínica PE',
            'direccion': 'Av. Test',
            'telefono': '01-1234567',
            'email': 'test@pe.com',
            'ruc': '12345678901',  # Válido: 11 dígitos
            'pais': 'PE',
            'moneda': 'PEN',
            'zona_horaria': 'America/Lima'
        }
        
        form = ClinicaForm(data=form_data)
        if not form.is_valid():
            print("Errores del formulario:", form.errors)  # Para debug
        self.assertTrue(form.is_valid())
    
    def test_sugerencia_moneda_segun_pais(self):
        """Test: advertencia si la moneda no corresponde al país"""
        form_data = {
            'nombre': 'Clínica Test',
            'direccion': 'Av. Test',
            'telefono': '02-1234567',
            'email': 'test@test.com',
            'pais': 'EC',  # Ecuador
            'moneda': 'PEN',  # Moneda peruana (incorrecta)
            'zona_horaria': 'America/Guayaquil'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('moneda', form.errors)
    
    def test_formulario_valido(self):
        """Test: formulario válido con datos mínimos requeridos"""
        form_data = {
            'nombre': 'Clínica Nueva',
            'direccion': 'Calle Principal 456',
            'telefono': '02-7654321',
            'email': 'nueva@clinica.com',
            'pais': 'EC',
            'moneda': 'USD',
            'zona_horaria': 'America/Guayaquil'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_email_duplicado(self):
        """Test: error si el email ya existe"""
        # Crear clínica existente
        Clinica.objects.create(
            nombre='Clínica Existente',
            direccion='Av. Existente 789',
            telefono='02-5555555',
            email='existente@clinica.com',
            uc=self.user
        )
        
        # Intentar crear otra con el mismo email
        form_data = {
            'nombre': 'Otra Clínica',
            'direccion': 'Otra Calle 123',
            'telefono': '02-6666666',
            'email': 'existente@clinica.com'  # Email duplicado
        }
        
        form = ClinicaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_formulario_telefono_corto(self):
        """Test: error si el teléfono es muy corto"""
        form_data = {
            'nombre': 'Clínica Test',
            'direccion': 'Calle Test',
            'telefono': '123',  # Muy corto
            'email': 'test@test.com'
        }
        
        form = ClinicaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)


class ClinicaViewsTest(MultiTenantTestCase):
    """Tests para las vistas de Clínica"""
    
    def setUp(self):
        super().setUp()  # Call parent setUp to get multi-tenant context
        
        # Upgrade user to staff for admin access
        self.user.is_staff = True
        self.user.save()
    
    def test_clinica_list_view(self):
        """Test: acceso a la vista de lista"""
        response = self.client.get(reverse('cit:clinica-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Clínicas')
        self.assertContains(response, 'Clinica Test')
    
    def test_clinica_detail_view(self):
        """Test: acceso a la vista de detalle"""
        response = self.client.get(
            reverse('cit:clinica-detail', kwargs={'pk': self.clinica.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clinica Test')
        self.assertContains(response, 'clinic@test.com')
    
    def test_clinica_create_view_get(self):
        """Test: acceso al formulario de creación"""
        response = self.client.get(reverse('cit:clinica-create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nueva Clínica')
    
    def test_clinica_update_view_get(self):
        """Test: acceso al formulario de edición"""
        response = self.client.get(
            reverse('cit:clinica-update', kwargs={'pk': self.clinica.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Clínica')
        self.assertContains(response, 'test@clinica.com')
    
    def test_clinica_delete_view_get(self):
        """Test: acceso a la vista de confirmación de eliminación"""
        response = self.client.get(
            reverse('cit:clinica-delete', kwargs={'pk': self.clinica.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirmar Eliminación')
    
    def test_clinica_delete_with_active_sucursales(self):
        """Test: no se puede eliminar clínica con sucursales activas"""
        # Crear sucursal activa
        Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Activa',
            direccion='Calle Activa',
            telefono='02-9999999',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            uc=self.user
        )
        
        response = self.client.post(
            reverse('cit:clinica-delete', kwargs={'pk': self.clinica.pk})
        )
        
        # Debe redirigir al detalle porque tiene sucursales activas
        self.assertEqual(response.status_code, 302)
        
        # La clínica sigue activa
        self.clinica.refresh_from_db()
        self.assertTrue(self.clinica.estado)
    
    def test_clinica_activate(self):
        """Test: reactivar una clínica desactivada"""
        # Desactivar la clínica primero
        self.clinica.estado = False
        self.clinica.save()
        
        # Reactivar la clínica
        response = self.client.post(
            reverse('cit:clinica-activate', kwargs={'pk': self.clinica.pk})
        )
        
        # Debe redirigir al detalle
        self.assertEqual(response.status_code, 302)
        
        # La clínica debe estar activa
        self.clinica.refresh_from_db()
        self.assertTrue(self.clinica.estado)
    
    def test_clinica_list_busqueda(self):
        """Test: buscar clínicas"""
        response = self.client.get(reverse('cit:clinica-list') + '?busqueda=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Clínica Test')
