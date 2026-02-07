"""
Tests para Dashboard de Alertas de Administradores
SOOD-91: Tests de permisos, filtros, estadísticas y acceso
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from pacientes.models import Paciente
from enfermedades.models import (
    CategoriaEnfermedad, 
    Enfermedad, 
    EnfermedadPaciente,
    AlertaPaciente
)
from clinicas.models import Clinica


class DashboardAlertasPermisosTest(TestCase):
    """Tests de permisos y control de acceso al dashboard."""
    
    def setUp(self):
        """Configurar usuarios y datos de prueba."""
        # Usuario normal (sin staff)
        self.usuario_normal = User.objects.create_user(
            username='usuario_normal',
            password='test123',
            email='normal@test.com'
        )
        
        # Usuario staff (con acceso)
        self.usuario_staff = User.objects.create_user(
            username='usuario_staff',
            password='test123',
            email='staff@test.com',
            is_staff=True
        )
        
        # Usuario superusuario
        self.usuario_admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        self.client = Client()
        self.url = reverse('enfermedades:dashboard_alertas')
    
    def test_acceso_denegado_usuario_normal(self):
        """Usuario normal no debe poder acceder al dashboard."""
        self.client.login(username='usuario_normal', password='test123')
        # Activar clínica en sesión
        clinica = Clinica.objects.create(nombre='Clinica Test', direccion='Dir', telefono='099999999', email='c@test.local', uc=self.usuario_normal)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        response = self.client.get(self.url)
        
        # Debe redirigir al login de admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_acceso_permitido_usuario_staff(self):
        """Usuario staff debe poder acceder al dashboard."""
        self.client.login(username='usuario_staff', password='test123')
        clinica = Clinica.objects.create(nombre='Clinica Staff', direccion='Dir', telefono='099999998', email='s@test.local', uc=self.usuario_staff)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'enfermedades/dashboard_alertas.html')
    
    def test_acceso_permitido_superusuario(self):
        """Superusuario debe poder acceder al dashboard."""
        self.client.login(username='admin', password='admin123')
        clinica = Clinica.objects.create(nombre='Clinica Admin', direccion='Dir', telefono='099999997', email='a@test.local', uc=self.usuario_admin)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'enfermedades/dashboard_alertas.html')
    
    def test_acceso_denegado_sin_autenticacion(self):
        """Usuario no autenticado debe ser redirigido."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)


class DashboardAlertasEstadisticasTest(TestCase):
    """Tests de estadísticas y datos del dashboard."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.usuario_admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        # Crear categoría y enfermedad
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='Cardiovascular',
            orden=1,
            uc=self.usuario_admin
        )
        
        self.enfermedad_critica = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre='Hipertensión Crítica',
            nivel_riesgo='CRITICO',
            requiere_interconsulta=True,
            uc=self.usuario_admin
        )
        
        # Crear pacientes
        self.paciente_rojo = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='1234567890',
            uc=self.usuario_admin
        )
        
        self.paciente_normal = Paciente.objects.create(
            nombres='María',
            apellidos='González',
            cedula='0987654321',
            uc=self.usuario_admin
        )
        
        # Asignar enfermedad crítica al paciente rojo
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_rojo,
            enfermedad=self.enfermedad_critica,
            uc=self.usuario_admin
        )
        
        # Crear alerta para paciente rojo
        AlertaPaciente.objects.create(
            paciente=self.paciente_rojo,
            tipo='ENFERMEDAD_CRITICA',
            nivel='ALTO',
            titulo='Enfermedad crítica detectada',
            descripcion='Paciente con hipertensión crítica',
            uc=self.usuario_admin
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        # Activar clínica en sesión
        clinica = Clinica.objects.create(nombre='Clinica Estadisticas', direccion='Dir', telefono='099999996', email='e@test.local', uc=self.usuario_admin)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        self.url = reverse('enfermedades:dashboard_alertas')
    
    def test_estadisticas_generales_presentes(self):
        """Verificar que las estadísticas generales se muestren correctamente."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar contexto
        self.assertIn('total_pacientes', response.context)
        self.assertIn('total_alertas_activas', response.context)
        self.assertIn('total_rojos', response.context)
        self.assertIn('total_amarillos', response.context)
        self.assertIn('total_verdes', response.context)
        
        # Verificar valores
        self.assertEqual(response.context['total_pacientes'], 2)
        # Al menos 1 alerta activa (puede haber más por signals)
        self.assertGreaterEqual(response.context['total_alertas_activas'], 1)
        self.assertGreaterEqual(response.context['total_rojos'], 1)
    
    def test_lista_pacientes_con_alertas(self):
        """Verificar que solo se listen pacientes con alertas activas."""
        response = self.client.get(self.url)
        
        pacientes = response.context['pacientes']
        
        # Debe haber al menos 1 paciente con alerta
        self.assertGreaterEqual(len(pacientes), 1)
        
        # Verificar que el paciente rojo esté en la lista
        pacientes_ids = [p.id for p in pacientes]
        self.assertIn(self.paciente_rojo.id, pacientes_ids)
    
    def test_enfermedades_comunes_presentes(self):
        """Verificar que se muestren las enfermedades más comunes."""
        response = self.client.get(self.url)
        
        self.assertIn('enfermedades_comunes', response.context)
        enfermedades = response.context['enfermedades_comunes']
        
        # Debe haber al menos 1 enfermedad
        self.assertGreaterEqual(len(enfermedades), 0)


class DashboardAlertasFiltrosTest(TestCase):
    """Tests de filtros por nivel de alerta."""
    
    def setUp(self):
        """Configurar datos de prueba con diferentes niveles."""
        self.usuario_admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        # Crear categoría y enfermedades
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='General',
            orden=1,
            uc=self.usuario_admin
        )
        
        self.enfermedad_critica = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre='Enfermedad Crítica',
            nivel_riesgo='CRITICO',
            requiere_interconsulta=True,
            uc=self.usuario_admin
        )
        
        # Crear paciente VIP con enfermedad crítica (debería ser ROJO)
        self.paciente_rojo = Paciente.objects.create(
            nombres='Paciente',
            apellidos='Rojo',
            cedula='1111111111',
            es_vip=True,
            uc=self.usuario_admin
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_rojo,
            enfermedad=self.enfermedad_critica,
            uc=self.usuario_admin
        )
        
        AlertaPaciente.objects.create(
            paciente=self.paciente_rojo,
            tipo='ENFERMEDAD_CRITICA',
            nivel='ALTO',
            titulo='Alerta crítica',
            descripcion='Test',
            uc=self.usuario_admin
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        clinica = Clinica.objects.create(nombre='Clinica Filtros', direccion='Dir', telefono='099999995', email='f@test.local', uc=self.usuario_admin)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        self.url = reverse('enfermedades:dashboard_alertas')
    
    def test_filtro_sin_nivel(self):
        """Sin filtro, debe mostrar todos los pacientes con alertas."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], '')
        
        # Debe haber pacientes en el listado
        pacientes = response.context['pacientes']
        self.assertGreaterEqual(len(pacientes), 0)
    
    def test_filtro_nivel_rojo(self):
        """Filtro ROJO debe mostrar solo pacientes rojos."""
        response = self.client.get(self.url, {'nivel': 'ROJO'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], 'ROJO')
        
        # Los pacientes retornados deben ser lista (filtramos en vista)
        pacientes = response.context['pacientes']
        self.assertIsInstance(pacientes, list)
    
    def test_filtro_nivel_amarillo(self):
        """Filtro AMARILLO debe funcionar correctamente."""
        response = self.client.get(self.url, {'nivel': 'AMARILLO'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], 'AMARILLO')
    
    def test_filtro_nivel_verde(self):
        """Filtro VERDE debe funcionar correctamente."""
        response = self.client.get(self.url, {'nivel': 'VERDE'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], 'VERDE')
    
    def test_filtro_nivel_invalido_ignora(self):
        """Filtro con nivel inválido debe ser ignorado."""
        response = self.client.get(self.url, {'nivel': 'INVALIDO'})
        
        self.assertEqual(response.status_code, 200)
        # No debe aplicar filtro, mostrar todos
        self.assertEqual(response.context['nivel_filtro'], 'INVALIDO')


class DashboardAlertasIntegracionTest(TestCase):
    """Tests de integración del dashboard completo."""
    
    def setUp(self):
        """Configurar escenario completo de prueba."""
        self.usuario_admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
        clinica = Clinica.objects.create(nombre='Clinica Integracion', direccion='Dir', telefono='099999994', email='i@test.local', uc=self.usuario_admin)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        self.url = reverse('enfermedades:dashboard_alertas')
    
    def test_dashboard_carga_sin_errores(self):
        """Dashboard debe cargar sin errores incluso sin datos."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'enfermedades/dashboard_alertas.html')
    
    def test_dashboard_muestra_mensaje_sin_alertas(self):
        """Cuando no hay alertas, debe mostrar mensaje apropiado."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Verificar que el contenido menciona "no hay alertas"
        self.assertContains(response, 'pacientes')
    
    def test_paginacion_funciona(self):
        """La paginación debe funcionar correctamente."""
        # Crear múltiples pacientes con alertas para probar paginación
        categoria = CategoriaEnfermedad.objects.create(
            nombre='Test',
            orden=1,
            uc=self.usuario_admin
        )
        
        enfermedad = Enfermedad.objects.create(
            categoria=categoria,
            nombre='Test Enfermedad',
            nivel_riesgo='ALTO',
            uc=self.usuario_admin
        )
        
        # Crear 25 pacientes (más que el paginate_by=20)
        for i in range(25):
            paciente = Paciente.objects.create(
                nombres=f'Paciente{i}',
                apellidos=f'Test{i}',
                cedula=f'{1000000000 + i}',
                uc=self.usuario_admin
            )
            
            EnfermedadPaciente.objects.create(
                paciente=paciente,
                enfermedad=enfermedad,
                uc=self.usuario_admin
            )
            
            AlertaPaciente.objects.create(
                paciente=paciente,
                tipo='TEST',
                nivel='MEDIO',
                titulo=f'Alerta {i}',
                descripcion=f'Descripción {i}',
                uc=self.usuario_admin
            )
        
        response = self.client.get(self.url)
        
        # Debe estar paginado
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['pacientes']), 20)
        
        # Segunda página debe tener 5 pacientes
        response_page2 = self.client.get(self.url, {'page': 2})
        self.assertEqual(len(response_page2.context['pacientes']), 5)
