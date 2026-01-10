"""
Tests para CalculadorAlerta y GestorAlertas
SOOD-78: Tests de CalculadorAlerta
SOOD-79: Tests de GestorAlertas
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from enfermedades.models import (
    CategoriaEnfermedad, Enfermedad, EnfermedadPaciente, AlertaPaciente
)
from enfermedades.utils import CalculadorAlerta, GestorAlertas
from pacientes.models import Paciente
from cit.models import Clinica


class CalculadorAlertaTestCase(TestCase):
    """Tests para la clase CalculadorAlerta"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Clínica de prueba
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            uc=self.user
        )
        
        # Paciente de prueba
        self.paciente = Paciente.objects.create(
            nombres='Juan',
            apellidos='Pérez',
            cedula='1234567890',
            uc=self.user
        )
        
        # Categoría de enfermedades
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='Cardiovasculares',
            descripcion='Enfermedades del sistema cardiovascular',
            uc=self.user
        )
        
        # Enfermedades de diferentes niveles
        self.enfermedad_critica = Enfermedad.objects.create(
            codigo_cie10='I21.0',
            nombre='Infarto Agudo de Miocardio',
            categoria=self.categoria,
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            requiere_interconsulta=True,
            uc=self.user
        )
        
        self.enfermedad_alto_riesgo = Enfermedad.objects.create(
            codigo_cie10='I10',
            nombre='Hipertensión Arterial',
            categoria=self.categoria,
            nivel_riesgo='ALTO',
            genera_alerta_roja=False,
            requiere_interconsulta=True,
            uc=self.user
        )
        
        self.enfermedad_medio_riesgo = Enfermedad.objects.create(
            codigo_cie10='E11',
            nombre='Diabetes Mellitus Tipo 2',
            categoria=self.categoria,
            nivel_riesgo='MEDIO',
            genera_alerta_roja=False,
            requiere_interconsulta=False,
            uc=self.user
        )
        
        self.enfermedad_bajo_riesgo = Enfermedad.objects.create(
            codigo_cie10='J30',
            nombre='Rinitis Alérgica',
            categoria=self.categoria,
            nivel_riesgo='BAJO',
            genera_alerta_roja=False,
            requiere_interconsulta=False,
            uc=self.user
        )
    
    def test_calculador_sin_enfermedades_retorna_verde(self):
        """Paciente sin enfermedades debe tener alerta VERDE"""
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        self.assertEqual(nivel, 'VERDE')
    
    def test_enfermedad_critica_genera_alerta_roja(self):
        """Paciente con enfermedad crítica debe tener alerta ROJA"""
        # Asociar enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        self.assertEqual(nivel, 'ROJO')
        
        # Verificar factores
        factores = calculador.obtener_factores_alerta()
        self.assertGreater(len(factores['ROJO']), 0)
        self.assertIn('Infarto Agudo de Miocardio', str(factores['ROJO']))
    
    def test_paciente_vip_genera_alerta_roja(self):
        """Paciente VIP debe tener alerta ROJA"""
        self.paciente.es_vip = True
        self.paciente.categoria_vip = 'PLATINUM'
        self.paciente.save()
        
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        self.assertEqual(nivel, 'ROJO')
        
        # Verificar factores
        factores = calculador.obtener_factores_alerta()
        self.assertGreater(len(factores['ROJO']), 0)
        self.assertTrue(
            any('VIP' in str(factor) for factor in factores['ROJO'])
        )
    
    def test_enfermedad_alto_riesgo_genera_alerta_amarilla(self):
        """Paciente con enfermedad de alto riesgo debe tener alerta AMARILLA"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_alto_riesgo,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        self.assertEqual(nivel, 'AMARILLO')
    
    def test_multiples_condiciones_genera_alerta_amarilla(self):
        """Paciente con múltiples enfermedades debe tener alerta AMARILLA"""
        # Crear 4 enfermedades de bajo riesgo
        for i in range(4):
            enfermedad = Enfermedad.objects.create(
                codigo_cie10=f'TEST{i}',
                nombre=f'Enfermedad Test {i}',
                categoria=self.categoria,
                nivel_riesgo='BAJO',
                uc=self.user
            )
            EnfermedadPaciente.objects.create(
                paciente=self.paciente,
                enfermedad=enfermedad,
                fecha_diagnostico=timezone.now().date(),
                estado_actual='ACTIVA',
                uc=self.user
            )
        
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        
        # Debe ser AMARILLO por múltiples condiciones
        self.assertEqual(nivel, 'AMARILLO')
        
        # Verificar factores
        factores = calculador.obtener_factores_alerta()
        self.assertTrue(
            any('Múltiples condiciones' in str(factor) for factor in factores['AMARILLO'])
        )
    
    def test_requiere_interconsulta_genera_alerta_amarilla(self):
        """Enfermedad que requiere interconsulta debe generar alerta AMARILLA"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_alto_riesgo,  # Requiere interconsulta
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        nivel = calculador.calcular_nivel_alerta()
        self.assertEqual(nivel, 'AMARILLO')
        
        factores = calculador.obtener_factores_alerta()
        self.assertTrue(
            any('interconsulta' in str(factor).lower() for factor in factores['AMARILLO'])
        )
    
    def test_determinar_tipo_alerta_enfermedad_critica(self):
        """Tipo de alerta debe ser ENFERMEDAD_CRITICA"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        tipo = calculador.determinar_tipo_alerta_principal()
        self.assertEqual(tipo, 'ENFERMEDAD_CRITICA')
    
    def test_determinar_tipo_alerta_vip_manual(self):
        """Tipo de alerta debe ser VIP_MANUAL para VIP marcado manualmente"""
        self.paciente.es_vip = True
        self.paciente.categoria_vip = 'PREMIUM'
        self.paciente.save()
        
        calculador = CalculadorAlerta(self.paciente)
        tipo = calculador.determinar_tipo_alerta_principal()
        self.assertEqual(tipo, 'VIP_MANUAL')
    
    def test_generar_titulo_alerta(self):
        """Debe generar un título descriptivo"""
        calculador = CalculadorAlerta(self.paciente)
        titulo = calculador.generar_titulo_alerta('ROJO', 'ENFERMEDAD_CRITICA')
        
        self.assertIn('CRÍTICO', titulo)
        self.assertIn(self.paciente.get_nombre_completo(), titulo)
    
    def test_generar_descripcion_alerta_verde(self):
        """Descripción para alerta VERDE debe indicar sin riesgos"""
        calculador = CalculadorAlerta(self.paciente)
        descripcion = calculador.generar_descripcion_alerta('VERDE')
        
        self.assertIn('sin factores de riesgo', descripcion.lower())
    
    def test_generar_descripcion_alerta_con_factores(self):
        """Descripción debe incluir factores identificados"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        descripcion = calculador.generar_descripcion_alerta('ROJO')
        
        self.assertIn('FACTORES CRÍTICOS', descripcion)
        self.assertIn('Infarto Agudo de Miocardio', descripcion)
    
    def test_get_resumen_estadistico(self):
        """Debe generar resumen estadístico correcto"""
        # Agregar enfermedades
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_alto_riesgo,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        calculador = CalculadorAlerta(self.paciente)
        resumen = calculador.get_resumen_estadistico()
        
        self.assertEqual(resumen['total_enfermedades'], 2)
        self.assertEqual(resumen['criticas'], 1)
        self.assertGreaterEqual(resumen['requieren_interconsulta'], 1)
    
    def test_cache_enfermedades_activas(self):
        """Debe cachear las consultas de enfermedades activas"""
        calculador = CalculadorAlerta(self.paciente)
        
        # Primera llamada
        enf1 = calculador.get_enfermedades_activas()
        # Segunda llamada debe retornar el mismo queryset (caché)
        enf2 = calculador.get_enfermedades_activas()
        
        self.assertIs(enf1, enf2, "Debe retornar el mismo objeto del caché")


class GestorAlertasTestCase(TestCase):
    """Tests para la clase GestorAlertas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            uc=self.user
        )
        
        self.paciente = Paciente.objects.create(
            nombres='María',
            apellidos='García',
            cedula='9876543210',
            uc=self.user
        )
        
        self.categoria = CategoriaEnfermedad.objects.create(
            nombre='Test',
            uc=self.user
        )
        
        self.enfermedad_critica = Enfermedad.objects.create(
            codigo_cie10='I21',
            nombre='Infarto',
            categoria=self.categoria,
            nivel_riesgo='CRITICO',
            genera_alerta_roja=True,
            uc=self.user
        )
    
    def test_crear_alerta_basica(self):
        """Debe crear una alerta básica correctamente"""
        gestor = GestorAlertas(self.paciente, self.user)
        
        alerta = gestor.crear_alerta(
            nivel='ROJO',
            tipo='ENFERMEDAD_CRITICA'
        )
        
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.paciente, self.paciente)
        self.assertEqual(alerta.nivel, 'ROJO')
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_CRITICA')
        self.assertTrue(alerta.es_activa)
        self.assertTrue(alerta.requiere_accion)
    
    def test_actualizar_alertas_sin_riesgos(self):
        """Paciente sin riesgos no debe crear alertas"""
        gestor = GestorAlertas(self.paciente, self.user)
        
        alerta, creada = gestor.actualizar_alertas()
        
        self.assertIsNone(alerta)
        self.assertFalse(creada)
    
    def test_actualizar_alertas_con_enfermedad_critica(self):
        """Debe crear alerta cuando hay enfermedad crítica"""
        # Asociar enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        alerta, creada = gestor.actualizar_alertas()
        
        self.assertIsNotNone(alerta)
        # Puede existir por señal previa; solo validamos que está activa y correcta
        self.assertFalse(creada)
        self.assertEqual(alerta.nivel, 'ROJO')
        self.assertEqual(alerta.tipo, 'ENFERMEDAD_CRITICA')
    
    def test_actualizar_alertas_no_duplica(self):
        """No debe duplicar alertas del mismo tipo"""
        # Crear enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        
        # Primera actualización (la señal ya pudo crearla)
        alerta1, creada1 = gestor.actualizar_alertas()
        self.assertFalse(creada1)
        
        # Segunda actualización
        alerta2, creada2 = gestor.actualizar_alertas()
        self.assertFalse(creada2)
        self.assertEqual(alerta1.id, alerta2.id)
    
    def test_actualizar_alertas_cambia_nivel(self):
        """Debe actualizar el nivel si cambia"""
        # Crear enfermedad de alto riesgo primero
        enfermedad_alta = Enfermedad.objects.create(
            codigo_cie10='I10',
            nombre='Hipertensión',
            categoria=self.categoria,
            nivel_riesgo='ALTO',
            uc=self.user
        )
        
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=enfermedad_alta,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        alerta1, _ = gestor.actualizar_alertas()
        self.assertEqual(alerta1.nivel, 'AMARILLO')
        
        # Agregar enfermedad crítica
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        alerta2, creada2 = gestor.actualizar_alertas()
        # La señal puede haber creado/actualizado; validamos estado final
        self.assertEqual(alerta2.nivel, 'ROJO')
        self.assertEqual(alerta2.tipo, 'ENFERMEDAD_CRITICA')
    
    def test_desactivar_alertas_activas(self):
        """Debe desactivar todas las alertas activas"""
        # Crear varias alertas
        AlertaPaciente.objects.create(
            paciente=self.paciente,
            nivel='ROJO',
            tipo='SISTEMA',
            titulo='Alerta 1',
            descripcion='Test',
            uc=self.user
        )
        AlertaPaciente.objects.create(
            paciente=self.paciente,
            nivel='AMARILLO',
            tipo='SISTEMA',
            titulo='Alerta 2',
            descripcion='Test',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        gestor.desactivar_alertas_activas(razon="Test de desactivación")
        
        alertas_activas = AlertaPaciente.objects.filter(
            paciente=self.paciente,
            es_activa=True
        )
        self.assertEqual(alertas_activas.count(), 0)
    
    def test_asociar_enfermedades_a_alerta(self):
        """Debe asociar enfermedades relevantes a la alerta"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        alerta, _ = gestor.actualizar_alertas()
        
        # Verificar que se asoció la enfermedad
        self.assertGreater(alerta.enfermedades_relacionadas.count(), 0)
        self.assertIn(
            self.enfermedad_critica,
            alerta.enfermedades_relacionadas.all()
        )
    
    def test_generar_reporte_alertas(self):
        """Debe generar un reporte completo"""
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        gestor.actualizar_alertas()
        
        reporte = gestor.generar_reporte_alertas()
        
        self.assertIn('paciente', reporte)
        self.assertIn('nivel_actual', reporte)
        self.assertIn('factores', reporte)
        self.assertIn('estadisticas', reporte)
        self.assertIn('alertas_activas', reporte)
        self.assertIn('recomendaciones', reporte)
        
        self.assertEqual(reporte['nivel_actual'], 'ROJO')
        self.assertGreater(len(reporte['alertas_activas']), 0)
    
    def test_recomendaciones_segun_nivel(self):
        """Debe generar recomendaciones apropiadas según el nivel"""
        # Nivel ROJO
        EnfermedadPaciente.objects.create(
            paciente=self.paciente,
            enfermedad=self.enfermedad_critica,
            fecha_diagnostico=timezone.now().date(),
            estado_actual='ACTIVA',
            uc=self.user
        )
        
        gestor = GestorAlertas(self.paciente, self.user)
        reporte = gestor.generar_reporte_alertas()
        
        recomendaciones = reporte['recomendaciones']
        self.assertGreater(len(recomendaciones), 0)
        self.assertTrue(
            any('prioritaria' in rec.lower() for rec in recomendaciones)
        )
