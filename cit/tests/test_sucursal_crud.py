"""
Tests para el CRUD de Sucursales
SOOD-48: CRUD de Sucursales - Implementar vistas y formularios
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from cit.models import Clinica, Sucursal, Cita
from cit.forms import SucursalForm
from datetime import time, datetime, timedelta
from django.utils import timezone


class SucursalModelTest(TestCase):
    """Tests para el modelo Sucursal"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user
        )
        
    def test_crear_sucursal(self):
        """Test: crear una sucursal con datos básicos"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Matriz',
            direccion='Av. Principal 100',
            telefono='02-9999999',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            dias_atencion='LMXJV',
            uc=self.user
        )
        
        self.assertEqual(sucursal.nombre, 'Matriz')
        self.assertEqual(sucursal.clinica, self.clinica)
        self.assertEqual(sucursal.dias_atencion, 'LMXJV')
        self.assertTrue(sucursal.estado)  # Activa por defecto
    
    def test_sucursal_str(self):
        """Test: representación en string de sucursal"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Norte',
            direccion='Av. Norte 200',
            telefono='02-8888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            dias_atencion='LMXJV',
            uc=self.user
        )
        
        self.assertEqual(str(sucursal), 'Clínica Test - Norte')
    
    def test_validacion_horarios(self):
        """Test: validar que horario_cierre > horario_apertura"""
        from django.core.exceptions import ValidationError
        
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Test',
            direccion='Av. Test',
            telefono='02-1111111',
            horario_apertura=time(18, 0),
            horario_cierre=time(8, 0),  # Cierre antes de apertura (inválido)
            dias_atencion='LMXJV',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError):
            sucursal.full_clean()
    
    def test_validacion_telefono_minimo(self):
        """Test: validar que teléfono tenga al menos 7 dígitos"""
        from django.core.exceptions import ValidationError
        
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Test',
            direccion='Av. Test',
            telefono='123',  # Menos de 7 dígitos (inválido)
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            dias_atencion='LMXJV',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError):
            sucursal.full_clean()
    
    def test_unique_together_nombre_clinica(self):
        """Test: no puede haber dos sucursales con mismo nombre en misma clínica"""
        from django.db import IntegrityError
        
        Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Matriz',
            direccion='Av. Test 1',
            telefono='02-1111111',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            dias_atencion='LMXJV',
            uc=self.user
        )
        
        with self.assertRaises(IntegrityError):
            Sucursal.objects.create(
                clinica=self.clinica,
                nombre='Matriz',  # Duplicado
                direccion='Av. Test 2',
                telefono='02-2222222',
                horario_apertura=time(8, 0),
                horario_cierre=time(18, 0),
                dias_atencion='LMXJV',
                uc=self.user
            )


class SucursalFormTest(TestCase):
    """Tests para el formulario de Sucursal"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user
        )
    
    def test_formulario_valido(self):
        """Test: formulario válido con todos los datos"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Norte',
            'direccion': 'Av. Norte 100',
            'telefono': '02-9876543',
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'dias_atencion_checkboxes': ['L', 'M', 'X', 'J', 'V']
        }
        
        form = SucursalForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_sin_dias_atencion(self):
        """Test: formulario inválido sin días de atención"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Test',
            'direccion': 'Av. Test',
            'telefono': '02-1234567',
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'dias_atencion_checkboxes': []  # Sin días
        }
        
        form = SucursalForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_formulario_horario_cierre_antes_apertura(self):
        """Test: formulario inválido cuando cierre < apertura"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Test',
            'direccion': 'Av. Test',
            'telefono': '02-1234567',
            'horario_apertura': '18:00',
            'horario_cierre': '08:00',  # Cierre antes de apertura
            'dias_atencion_checkboxes': ['L', 'M', 'X']
        }
        
        form = SucursalForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_formulario_telefono_corto(self):
        """Test: formulario inválido con teléfono < 7 dígitos"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Test',
            'direccion': 'Av. Test',
            'telefono': '12345',  # Menos de 7 dígitos
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'dias_atencion_checkboxes': ['L', 'M']
        }
        
        form = SucursalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)
    
    def test_conversion_dias_atencion(self):
        """Test: conversión de checkboxes a string en orden correcto"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Test',
            'direccion': 'Av. Test',
            'telefono': '02-1234567',
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'dias_atencion_checkboxes': ['V', 'L', 'X', 'M']  # Desordenados
        }
        
        form = SucursalForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Debe ordenarse como LMXV
        self.assertEqual(form.cleaned_data['dias_atencion'], 'LMXV')


class SucursalViewsTest(TestCase):
    """Tests para las vistas CRUD de Sucursal"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user
        )
        
        self.sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Matriz',
            direccion='Av. Principal 100',
            telefono='02-9999999',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            dias_atencion='LMXJV',
            uc=self.user
        )
    
    def test_sucursal_list_view(self):
        """Test: vista de lista de sucursales"""
        response = self.client.get(reverse('cit:sucursal-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matriz')
        self.assertTemplateUsed(response, 'cit/sucursal_list.html')
    
    def test_sucursal_list_filtro_clinica(self):
        """Test: filtro por clínica en lista de sucursales"""
        # Crear otra clínica y sucursal
        clinica2 = Clinica.objects.create(
            nombre='Clínica 2',
            direccion='Av. Test 456',
            telefono='02-7654321',
            email='test2@clinica.com',
            uc=self.user
        )
        
        Sucursal.objects.create(
            clinica=clinica2,
            nombre='Sur',
            direccion='Av. Sur 200',
            telefono='02-8888888',
            horario_apertura=time(9, 0),
            horario_cierre=time(17, 0),
            dias_atencion='LMXJ',
            uc=self.user
        )
        
        response = self.client.get(
            reverse('cit:sucursal-list'),
            {'clinica': self.clinica.id}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matriz')
        self.assertNotContains(response, 'Sur')
    
    def test_sucursal_detail_view(self):
        """Test: vista de detalle de sucursal"""
        response = self.client.get(
            reverse('cit:sucursal-detail', kwargs={'pk': self.sucursal.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matriz')
        self.assertContains(response, '02-9999999')
        self.assertTemplateUsed(response, 'cit/sucursal_detail.html')
    
    def test_sucursal_create_view_get(self):
        """Test: GET a vista de creación de sucursal"""
        response = self.client.get(reverse('cit:sucursal-create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/sucursal_form.html')
    
    def test_sucursal_create_view_post(self):
        """Test: POST a vista de creación de sucursal"""
        data = {
            'clinica': self.clinica.id,
            'nombre': 'Norte',
            'direccion': 'Av. Norte 500',
            'telefono': '02-7777777',
            'horario_apertura': '09:00',
            'horario_cierre': '19:00',
            'dias_atencion_checkboxes': ['L', 'M', 'X', 'J', 'V']
        }
        
        response = self.client.post(reverse('cit:sucursal-create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(
            Sucursal.objects.filter(nombre='Norte', clinica=self.clinica).exists()
        )
    
    def test_sucursal_update_view_get(self):
        """Test: GET a vista de edición de sucursal"""
        response = self.client.get(
            reverse('cit:sucursal-update', kwargs={'pk': self.sucursal.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/sucursal_form.html')
        self.assertContains(response, 'Matriz')
    
    def test_sucursal_update_view_post(self):
        """Test: POST a vista de edición de sucursal"""
        data = {
            'clinica': self.clinica.id,
            'nombre': 'Matriz Actualizada',
            'direccion': 'Av. Principal 100',
            'telefono': '02-9999999',
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'dias_atencion_checkboxes': ['L', 'M', 'X', 'J', 'V']
        }
        
        response = self.client.post(
            reverse('cit:sucursal-update', kwargs={'pk': self.sucursal.pk}),
            data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.sucursal.refresh_from_db()
        self.assertEqual(self.sucursal.nombre, 'Matriz Actualizada')
    
    def test_sucursal_delete_view_get(self):
        """Test: GET a vista de confirmación de eliminación"""
        response = self.client.get(
            reverse('cit:sucursal-delete', kwargs={'pk': self.sucursal.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/sucursal_confirm_delete.html')
    
    def test_sucursal_delete_view_post(self):
        """Test: POST a vista de eliminación (soft delete)"""
        sucursal_pk = self.sucursal.pk
        
        response = self.client.post(
            reverse('cit:sucursal-delete', kwargs={'pk': sucursal_pk})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        # Obtener la sucursal desactivada directamente
        sucursal_desactivada = Sucursal.objects.get(pk=sucursal_pk)
        self.assertFalse(sucursal_desactivada.estado)  # Desactivada
    
    def test_sucursal_activate_view_post(self):
        """Test: POST a vista de reactivación"""
        # Primero desactivar
        self.sucursal.estado = False
        self.sucursal.save()
        
        response = self.client.post(
            reverse('cit:sucursal-activate', kwargs={'pk': self.sucursal.pk})
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.sucursal.refresh_from_db()
        self.assertTrue(self.sucursal.estado)  # Reactivada
    
    def test_login_required_views(self):
        """Test: vistas requieren autenticación"""
        self.client.logout()
        
        views_to_test = [
            reverse('cit:sucursal-list'),
            reverse('cit:sucursal-create'),
            reverse('cit:sucursal-detail', kwargs={'pk': self.sucursal.pk}),
            reverse('cit:sucursal-update', kwargs={'pk': self.sucursal.pk}),
            reverse('cit:sucursal-delete', kwargs={'pk': self.sucursal.pk}),
        ]
        
        for url in views_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirect a login


class SucursalHorariosDiferenciadosTest(TestCase):
    """Tests para horarios diferenciados (sábado/domingo) - SOOD-48"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Av. Test 123',
            telefono='02-1234567',
            email='test@clinica.com',
            uc=self.user
        )
        
    def test_sabado_horario_diferenciado_valido(self):
        """Test: sucursal con horario diferenciado para sábado"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Test',
            direccion='Av. Test 100',
            telefono='02-9999999',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            sabado_horario_apertura=time(8, 0),
            sabado_horario_cierre=time(13, 0),  # Cierra al mediodía sábados
            dias_atencion='LMXJVS',
            uc=self.user
        )
        
        self.assertEqual(sucursal.sabado_horario_apertura, time(8, 0))
        self.assertEqual(sucursal.sabado_horario_cierre, time(13, 0))
        
        # Verificar método get_horario_dia
        horario_lunes = sucursal.get_horario_dia('L')
        self.assertEqual(horario_lunes['apertura'], time(8, 0))
        self.assertEqual(horario_lunes['cierre'], time(18, 0))
        
        horario_sabado = sucursal.get_horario_dia('S')
        self.assertEqual(horario_sabado['apertura'], time(8, 0))
        self.assertEqual(horario_sabado['cierre'], time(13, 0))
    
    def test_domingo_horario_diferenciado_valido(self):
        """Test: sucursal con horario diferenciado para domingo"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal 24/7',
            direccion='Av. Test 200',
            telefono='02-8888888',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            domingo_horario_apertura=time(9, 0),
            domingo_horario_cierre=time(14, 0),
            dias_atencion='LMXJVSD',
            uc=self.user
        )
        
        horario_domingo = sucursal.get_horario_dia('D')
        self.assertEqual(horario_domingo['apertura'], time(9, 0))
        self.assertEqual(horario_domingo['cierre'], time(14, 0))
    
    def test_horarios_diferenciados_ambos_dias(self):
        """Test: sucursal con horarios diferenciados para sábado Y domingo"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Completa',
            direccion='Av. Test 300',
            telefono='02-7777777',
            horario_apertura=time(8, 0),
            horario_cierre=time(20, 0),
            sabado_horario_apertura=time(8, 0),
            sabado_horario_cierre=time(13, 0),
            domingo_horario_apertura=time(10, 0),
            domingo_horario_cierre=time(12, 0),
            dias_atencion='LMXJVSD',
            uc=self.user
        )
        
        # L-V usa horario general
        self.assertEqual(sucursal.get_horario_dia('M')['cierre'], time(20, 0))
        # Sábado usa horario específico
        self.assertEqual(sucursal.get_horario_dia('S')['cierre'], time(13, 0))
        # Domingo usa horario específico
        self.assertEqual(sucursal.get_horario_dia('D')['cierre'], time(12, 0))
    
    def test_sabado_sin_horario_usa_general(self):
        """Test: si no se especifica horario sábado, usa el general"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Standard',
            direccion='Av. Test 400',
            telefono='02-6666666',
            horario_apertura=time(9, 0),
            horario_cierre=time(17, 0),
            # NO especifica sabado_horario_*
            dias_atencion='LMXJVS',
            uc=self.user
        )
        
        horario_sabado = sucursal.get_horario_dia('S')
        # Debe usar horario general
        self.assertEqual(horario_sabado['apertura'], time(9, 0))
        self.assertEqual(horario_sabado['cierre'], time(17, 0))
    
    def test_validacion_sabado_cierre_antes_apertura(self):
        """Test: validar que horario cierre sábado > apertura sábado"""
        from django.core.exceptions import ValidationError
        
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Inválida',
            direccion='Av. Test 500',
            telefono='02-5555555',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            sabado_horario_apertura=time(13, 0),  # Abre a la 1pm
            sabado_horario_cierre=time(9, 0),     # ❌ Cierra a las 9am (inválido)
            dias_atencion='LMXJVS',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            sucursal.full_clean()
        
        self.assertIn('sábado', str(context.exception).lower())
    
    def test_validacion_domingo_cierre_antes_apertura(self):
        """Test: validar que horario cierre domingo > apertura domingo"""
        from django.core.exceptions import ValidationError
        
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Inválida 2',
            direccion='Av. Test 600',
            telefono='02-4444444',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            domingo_horario_apertura=time(12, 0),
            domingo_horario_cierre=time(10, 0),  # ❌ Inválido
            dias_atencion='LMXJVD',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            sucursal.full_clean()
        
        self.assertIn('domingo', str(context.exception).lower())
    
    def test_validacion_sabado_parcial_invalido(self):
        """Test: si se especifica horario sábado, AMBOS campos son requeridos"""
        from django.core.exceptions import ValidationError
        
        # Solo apertura, sin cierre
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Parcial',
            direccion='Av. Test 700',
            telefono='02-3333333',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            sabado_horario_apertura=time(8, 0),  # Especifica apertura
            sabado_horario_cierre=None,          # ❌ Falta cierre
            dias_atencion='LMXJVS',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            sucursal.full_clean()
        
        # Verificar que el mensaje incluya la validación de sábado
        error_msg = str(context.exception).lower()
        self.assertTrue(
            'sábado' in error_msg or 'sabado' in error_msg,
            f"Expected 'sábado' in error message, got: {error_msg}"
        )
    
    def test_validacion_domingo_parcial_invalido(self):
        """Test: si se especifica horario domingo, AMBOS campos son requeridos"""
        from django.core.exceptions import ValidationError
        
        # Solo cierre, sin apertura
        sucursal = Sucursal(
            clinica=self.clinica,
            nombre='Sucursal Parcial 2',
            direccion='Av. Test 800',
            telefono='02-2222222',
            horario_apertura=time(8, 0),
            horario_cierre=time(18, 0),
            domingo_horario_apertura=None,       # ❌ Falta apertura
            domingo_horario_cierre=time(14, 0),  # Especifica cierre
            dias_atencion='LMXJVD',
            uc=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            sucursal.full_clean()
        
        # Verificar que el mensaje incluya la validación de domingo
        error_msg = str(context.exception).lower()
        self.assertTrue(
            'domingo' in error_msg,
            f"Expected 'domingo' in error message, got: {error_msg}"
        )
    
    def test_form_horarios_diferenciados_validos(self):
        """Test: formulario con horarios diferenciados válidos"""
        form_data = {
            'clinica': self.clinica.id,
            'nombre': 'Sucursal Form Test',
            'direccion': 'Av. Form 100',
            'telefono': '02-1111111',
            'horario_apertura': '08:00',
            'horario_cierre': '18:00',
            'sabado_horario_apertura': '08:00',
            'sabado_horario_cierre': '13:00',
            'domingo_horario_apertura': '09:00',
            'domingo_horario_cierre': '14:00',
            'dias_atencion_checkboxes': ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        }
        
        form = SucursalForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        
        sucursal = form.save(commit=False)
        sucursal.uc = self.user
        sucursal.save()
        
        self.assertEqual(sucursal.sabado_horario_apertura, time(8, 0))
        self.assertEqual(sucursal.sabado_horario_cierre, time(13, 0))
    
    def test_get_horario_dia_todos_los_dias(self):
        """Test: método get_horario_dia() para todos los días de la semana"""
        sucursal = Sucursal.objects.create(
            clinica=self.clinica,
            nombre='Sucursal Completa',
            direccion='Av. Test 900',
            telefono='02-0000000',
            horario_apertura=time(8, 0),
            horario_cierre=time(20, 0),
            sabado_horario_apertura=time(9, 0),
            sabado_horario_cierre=time(15, 0),
            domingo_horario_apertura=time(10, 0),
            domingo_horario_cierre=time(14, 0),
            dias_atencion='LMXJVSD',
            uc=self.user
        )
        
        # L-V usan horario general
        for dia in ['L', 'M', 'X', 'J', 'V']:
            horario = sucursal.get_horario_dia(dia)
            self.assertEqual(horario['apertura'], time(8, 0))
            self.assertEqual(horario['cierre'], time(20, 0))
        
        # Sábado usa horario específico
        horario_s = sucursal.get_horario_dia('S')
        self.assertEqual(horario_s['apertura'], time(9, 0))
        self.assertEqual(horario_s['cierre'], time(15, 0))
        
        # Domingo usa horario específico
        horario_d = sucursal.get_horario_dia('D')
        self.assertEqual(horario_d['apertura'], time(10, 0))
        self.assertEqual(horario_d['cierre'], time(14, 0))
