"""
Tests unitarios para DashboardAlertasView (SOOD-91)
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from pacientes.models import Paciente
from enfermedades.models import Enfermedad, CategoriaEnfermedad, EnfermedadPaciente, AlertaPaciente
from datetime import date, timedelta
from clinicas.models import Clinica


class DashboardAlertasViewTests(TestCase):
    """Tests para el Dashboard de Alertas (solo staff)."""
    
    def setUp(self):
        """Configuración inicial para todos los tests."""
        self.client = Client()
        # Activar clínica en sesión para satisfacer middleware multi-tenant
        clinica = Clinica.objects.create(nombre='Clinica Dashboard', direccion='Dir', telefono='099999993', email='d@test.local', uc=User.objects.create_user(username='owner_dash'))
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        
        # Crear usuarios
        self.staff_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.normal_user = User.objects.create_user(
            username='doctor',
            password='doctor123',
            is_staff=False
        )
        
        # Crear categoría de enfermedad
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre="Cardiovasculares",
            orden=1,
            uc=self.staff_user
        )
        
        # Crear enfermedades con diferentes niveles de riesgo
        self.enfermedad_critica = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hemofilia",
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            uc=self.staff_user
        )
        
        self.enfermedad_alta = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Hipertensión Arterial",
            nivel_riesgo='ALTO',
            genera_alerta_amarilla=True,
            uc=self.staff_user
        )
        
        self.enfermedad_media = Enfermedad.objects.create(
            categoria=self.categoria,
            nombre="Diabetes Tipo 2",
            nivel_riesgo='MEDIO',
            uc=self.staff_user
        )
        
        # Crear pacientes
        self.paciente_critico = Paciente.objects.create(
            nombres="Juan",
            apellidos="Pérez",
            cedula="1234567890",
            fecha_nacimiento=date.today() - timedelta(days=365*30),
            uc=self.staff_user
        )
        
        self.paciente_vip = Paciente.objects.create(
            nombres="María",
            apellidos="González",
            cedula="0987654321",
            fecha_nacimiento=date.today() - timedelta(days=365*40),
            es_vip=True,
            categoria_vip='PLATINUM',
            uc=self.staff_user
        )
        
        self.paciente_normal = Paciente.objects.create(
            nombres="Pedro",
            apellidos="Ramírez",
            cedula="1122334455",
            fecha_nacimiento=date.today() - timedelta(days=365*25),
            uc=self.staff_user
        )
        
        # Asignar enfermedades
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_critico,
            enfermedad=self.enfermedad_critica,
            uc=self.staff_user
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente_critico,
            enfermedad=self.enfermedad_alta,
            uc=self.staff_user
        )
        
        # Crear alertas
        AlertaPaciente.objects.create(
            paciente=self.paciente_critico,
            nivel='ROJO',
            tipo='ENFERMEDAD_CRITICA',
            descripcion='Paciente con hemofilia',
            es_activa=True,
            uc=self.staff_user
        )
        
        AlertaPaciente.objects.create(
            paciente=self.paciente_vip,
            nivel='ROJO',
            tipo='VIP_MANUAL',
            descripcion='Paciente VIP Platinum',
            es_activa=True,
            uc=self.staff_user
        )
    
    def test_acceso_solo_staff(self):
        """Solo usuarios staff pueden acceder al dashboard."""
        url = reverse('enfermedades:dashboard_alertas')
        
        # Sin login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect a login
        
        # Usuario normal (no staff)
        self.client.login(username='doctor', password='doctor123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Usuario staff
        self.client.login(username='admin', password='admin123')
        # Re-activar clínica tras login (el login puede resetear sesión)
        clinica = Clinica.objects.create(nombre='Clinica Dashboard Staff', direccion='Dir', telefono='099999992', email='ds@test.local', uc=self.staff_user)
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_muestra_estadisticas(self):
        """El dashboard muestra estadísticas correctas."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard de Alertas')
        
        # Verificar contexto
        self.assertIn('total_alertas_activas', response.context)
        self.assertIn('total_rojos', response.context)
        self.assertIn('total_amarillos', response.context)
        self.assertIn('total_vips', response.context)
        
        # Debe haber alertas activas (al menos las 2 que creamos)
        self.assertGreaterEqual(response.context['total_alertas_activas'], 2)
        
        # Debe haber 1 VIP
        self.assertEqual(response.context['total_vips'], 1)
    
    def test_filtro_por_nivel_rojo(self):
        """Filtro por nivel ROJO funciona correctamente."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas') + '?nivel=ROJO'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('nivel_filtro', response.context)
        self.assertEqual(response.context['nivel_filtro'], 'ROJO')
        
        # Debe mostrar solo pacientes con nivel ROJO
        pacientes = response.context['pacientes']
        for paciente in pacientes:
            self.assertEqual(paciente.nivel_alerta, 'ROJO')
    
    def test_filtro_por_nivel_amarillo(self):
        """Filtro por nivel AMARILLO funciona correctamente."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas') + '?nivel=AMARILLO'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], 'AMARILLO')
    
    def test_filtro_por_nivel_verde(self):
        """Filtro por nivel VERDE funciona correctamente."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas') + '?nivel=VERDE'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], 'VERDE')
    
    def test_dashboard_sin_filtro_muestra_todos(self):
        """Sin filtro, muestra todos los pacientes con alertas."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nivel_filtro'], '')
        
        # Debe mostrar pacientes con alertas activas
        pacientes = list(response.context['pacientes'])
        self.assertGreater(len(pacientes), 0)
    
    def test_paginacion_funciona(self):
        """La paginación funciona correctamente."""
        # Crear muchos pacientes para probar paginación
        for i in range(25):
            paciente = Paciente.objects.create(
                nombres=f"Paciente{i}",
                apellidos=f"Test{i}",
                cedula=f"999{i:04d}",
                fecha_nacimiento=date.today() - timedelta(days=365*30),
                uc=self.staff_user
            )
            AlertaPaciente.objects.create(
                paciente=paciente,
                nivel='VERDE',
                tipo='SISTEMA',
                descripcion='Test',
                es_activa=True,
                uc=self.staff_user
            )
        
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
    
    def test_enfermedades_comunes_en_contexto(self):
        """El contexto incluye enfermedades comunes."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('enfermedades_comunes', response.context)
    
    def test_semaforo_clase_correcta(self):
        """Los pacientes se muestran correctamente en el dashboard."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto tiene los datos necesarios
        self.assertIn('pacientes', response.context)
        
        # Verificar que se usan las clases CSS correctas en el template
        # (el nivel_alerta se calcula en el template con la etiqueta nivel_alerta)
        self.assertContains(response, 'semaforo-')
    
    def test_template_correcto(self):
        """Se usa el template correcto."""
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'enfermedades/dashboard_alertas.html')
    
    def test_sin_alertas_activas_muestra_mensaje(self):
        """Si no hay alertas activas, muestra mensaje apropiado."""
        # Desactivar todas las alertas
        AlertaPaciente.objects.all().update(es_activa=False)
        
        self.client.login(username='admin', password='admin123')
        url = reverse('enfermedades:dashboard_alertas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '¡Excelente!')
