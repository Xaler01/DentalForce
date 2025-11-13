"""
Tests para el CRUD de Especialidades
JIRA: SOOD-29
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from cit.models import Especialidad
from cit.forms import EspecialidadForm

User = get_user_model()


class EspecialidadModelTest(TestCase):
    """Tests para el modelo Especialidad"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear usuario para uc (usuario creador)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.especialidad = Especialidad.objects.create(
            nombre="Ortodoncia",
            descripcion="Especialidad enfocada en la corrección dental",
            duracion_default=45,
            color_calendario="#ff5733",
            estado=True,
            uc=self.user  # Usuario creador requerido
        )
    
    def test_especialidad_creacion(self):
        """Test: crear especialidad correctamente"""
        self.assertEqual(self.especialidad.nombre, "Ortodoncia")
        self.assertEqual(self.especialidad.duracion_default, 45)
        self.assertTrue(self.especialidad.estado)
    
    def test_especialidad_str(self):
        """Test: representación en string del modelo"""
        self.assertEqual(str(self.especialidad), "Ortodoncia")
    
    def test_nombre_unico(self):
        """Test: validar que el nombre sea único"""
        with self.assertRaises(Exception):
            Especialidad.objects.create(
                nombre="Ortodoncia",  # Nombre duplicado
                duracion_default=30,
                uc=self.user
            )
    
    def test_color_default(self):
        """Test: color por defecto es #3498db"""
        especialidad_sin_color = Especialidad.objects.create(
            nombre="Endodoncia",
            duracion_default=60,
            uc=self.user
        )
        self.assertEqual(especialidad_sin_color.color_calendario, '#3498db')
    
    def test_duracion_default_value(self):
        """Test: duración por defecto es 30 minutos"""
        especialidad = Especialidad.objects.create(
            nombre="Periodoncia",
            uc=self.user
        )
        self.assertEqual(especialidad.duracion_default, 30)


class EspecialidadFormTest(TestCase):
    """Tests para el formulario EspecialidadForm"""
    
    def setUp(self):
        """Crear usuario y especialidad existente para tests de unicidad"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.especialidad_existente = Especialidad.objects.create(
            nombre="Implantología",
            duracion_default=90,
            uc=self.user
        )
    
    def test_form_valido(self):
        """Test: formulario con datos válidos"""
        form_data = {
            'nombre': 'Estética Dental',
            'descripcion': 'Mejora la apariencia de los dientes',
            'duracion_default': 60,
            'color_calendario': '#2ecc71',
            'estado': True
        }
        form = EspecialidadForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_nombre_muy_corto(self):
        """Test: rechazar nombre con menos de 3 caracteres"""
        form_data = {
            'nombre': 'Ab',  # Solo 2 caracteres
            'duracion_default': 30,
            'color_calendario': '#3498db',
        }
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)
    
    def test_nombre_duplicado(self):
        """Test: rechazar nombre duplicado (case-insensitive)"""
        form_data = {
            'nombre': 'implantología',  # Existe "Implantología"
            'duracion_default': 30,
            'color_calendario': '#3498db',
        }
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)
    
    def test_duracion_no_multiplo_15(self):
        """Test: rechazar duración que no sea múltiplo de 15"""
        form_data = {
            'nombre': 'Cirugía Oral',
            'duracion_default': 40,  # No es múltiplo de 15
            'color_calendario': '#e74c3c',
        }
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('duracion_default', form.errors)
    
    def test_duracion_fuera_rango(self):
        """Test: rechazar duración menor a 15 o mayor a 240"""
        # Menor a 15
        form_data = {
            'nombre': 'Test1',
            'duracion_default': 10,
            'color_calendario': '#3498db',
        }
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Mayor a 240
        form_data['nombre'] = 'Test2'
        form_data['duracion_default'] = 300
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_color_sin_hashtag(self):
        """Test: agregar # automáticamente al color"""
        form_data = {
            'nombre': 'Odontopediatría',
            'duracion_default': 30,
            'color_calendario': '9b59b6',  # Sin #
        }
        form = EspecialidadForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['color_calendario'], '#9b59b6')
    
    def test_color_formato_invalido(self):
        """Test: rechazar color con formato inválido"""
        form_data = {
            'nombre': 'Test',
            'duracion_default': 30,
            'color_calendario': 'rojo',  # No es hex
        }
        form = EspecialidadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('color_calendario', form.errors)
    
    def test_nombre_capitalizado(self):
        """Test: nombre se capitaliza automáticamente"""
        form_data = {
            'nombre': 'rehabilitación oral',
            'duracion_default': 45,
            'color_calendario': '#16a085',
        }
        form = EspecialidadForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nombre'], 'Rehabilitación Oral')


class EspecialidadViewsTest(TestCase):
    """Tests para las vistas del CRUD de Especialidades"""
    
    def setUp(self):
        """Configuración inicial: crear usuario y especialidades"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Crear especialidades de prueba
        self.especialidad1 = Especialidad.objects.create(
            nombre="Endodoncia",
            descripcion="Tratamiento de conductos",
            duracion_default=60,
            color_calendario="#e74c3c",
            uc=self.user
        )
        self.especialidad2 = Especialidad.objects.create(
            nombre="Periodoncia",
            duracion_default=45,
            color_calendario="#3498db",
            estado=False,  # Inactiva
            uc=self.user
        )
    
    def test_list_view_get(self):
        """Test: cargar vista de listado"""
        url = reverse('cit:especialidad-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Endodoncia")
        self.assertTemplateUsed(response, 'cit/especialidad_list.html')
    
    def test_list_view_busqueda(self):
        """Test: buscar especialidades por nombre"""
        url = reverse('cit:especialidad-list')
        response = self.client.get(url, {'q': 'endo'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Endodoncia")
        self.assertNotContains(response, "Periodoncia")
    
    def test_list_view_filtro_estado(self):
        """Test: filtrar por estado (activas/inactivas)"""
        url = reverse('cit:especialidad-list')
        
        # Filtrar activas
        response = self.client.get(url, {'estado': 'activas'})
        self.assertContains(response, "Endodoncia")
        self.assertNotContains(response, "Periodoncia")
        
        # Filtrar inactivas
        response = self.client.get(url, {'estado': 'inactivas'})
        self.assertNotContains(response, "Endodoncia")
        self.assertContains(response, "Periodoncia")
    
    def test_create_view_get(self):
        """Test: cargar formulario de creación"""
        url = reverse('cit:especialidad-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/especialidad_form.html')
        self.assertContains(response, "Nueva Especialidad")
    
    def test_create_view_post_valido(self):
        """Test: crear especialidad con datos válidos"""
        url = reverse('cit:especialidad-create')
        data = {
            'nombre': 'Cirugía Maxilofacial',
            'descripcion': 'Cirugía de maxilares',
            'duracion_default': 120,
            'color_calendario': '#8e44ad',
            'estado': True
        }
        response = self.client.post(url, data)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó en base de datos
        self.assertTrue(
            Especialidad.objects.filter(nombre='Cirugía Maxilofacial').exists()
        )
    
    def test_create_view_post_invalido(self):
        """Test: rechazar creación con datos inválidos"""
        url = reverse('cit:especialidad-create')
        data = {
            'nombre': 'Ab',  # Muy corto
            'duracion_default': 40,  # No es múltiplo de 15
            'color_calendario': 'azul',  # Formato inválido
        }
        response = self.client.post(url, data)
        
        # No debe redirigir (hay errores)
        self.assertEqual(response.status_code, 200)
        # Verificar que el formulario tiene errores
        self.assertFalse(response.context['form'].is_valid())
        # Verificar que hay errores en campos específicos
        self.assertIn('nombre', response.context['form'].errors)
        self.assertIn('duracion_default', response.context['form'].errors)
        self.assertIn('color_calendario', response.context['form'].errors)
    
    def test_update_view_get(self):
        """Test: cargar formulario de edición"""
        url = reverse('cit:especialidad-update', kwargs={'pk': self.especialidad1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/especialidad_form.html')
        self.assertContains(response, "Endodoncia")
    
    def test_update_view_post_valido(self):
        """Test: actualizar especialidad con datos válidos"""
        url = reverse('cit:especialidad-update', kwargs={'pk': self.especialidad1.pk})
        data = {
            'nombre': 'Endodoncia Avanzada',  # Nombre actualizado
            'descripcion': 'Tratamiento de conductos complejos',
            'duracion_default': 90,
            'color_calendario': '#c0392b',
            'estado': True
        }
        response = self.client.post(url, data)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar cambios en DB
        self.especialidad1.refresh_from_db()
        self.assertEqual(self.especialidad1.nombre, 'Endodoncia Avanzada')
        self.assertEqual(self.especialidad1.duracion_default, 90)
    
    def test_delete_view_get(self):
        """Test: cargar confirmación de eliminación"""
        url = reverse('cit:especialidad-delete', kwargs={'pk': self.especialidad1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cit/especialidad_confirm_delete.html')
        self.assertContains(response, "Desactivar")
    
    def test_delete_view_post_soft_delete(self):
        """Test: desactivar (soft delete) especialidad"""
        url = reverse('cit:especialidad-delete', kwargs={'pk': self.especialidad1.pk})
        response = self.client.post(url)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que no se eliminó de DB, solo se desactivó
        self.especialidad1.refresh_from_db()
        self.assertFalse(self.especialidad1.estado)  # estado = False
        self.assertTrue(
            Especialidad.objects.filter(pk=self.especialidad1.pk).exists()
        )
    
    def test_paginacion(self):
        """Test: paginación funciona correctamente"""
        # Crear 15 especialidades adicionales
        for i in range(15):
            Especialidad.objects.create(
                nombre=f"Especialidad Test {i}",
                duracion_default=30,
                uc=self.user
            )
        
        url = reverse('cit:especialidad-list')
        response = self.client.get(url)
        
        # Verificar que hay paginación (10 por página)
        self.assertEqual(len(response.context['especialidades']), 10)
        self.assertTrue(response.context['is_paginated'])
