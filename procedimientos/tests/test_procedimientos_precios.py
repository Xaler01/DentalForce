"""
Pruebas unitarias para el módulo de procedimientos odontológicos.

Cubre:
- ProcedimientoOdontologico: Catálogo maestro
- ClinicaProcedimiento: Precios por clínica
- Métodos: get_precio_para_clinica(), validaciones
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

from procedimientos.models import (
    ProcedimientoOdontologico,
    ClinicaProcedimiento
)
from clinicas.models import Clinica


class ProcedimientoOdontologicoTestCase(TestCase):
    """Pruebas para el modelo ProcedimientoOdontologico"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.procedimiento = ProcedimientoOdontologico.objects.create(
            codigo='RES-OBT001',
            codigo_cdt='D2140',
            nombre='Obturación con Resina',
            descripcion='Restauración con resina compuesta',
            categoria='RESTAURATIVA',
            duracion_estimada=45,
            requiere_anestesia=True,
            afecta_odontograma=True,
            estado=True,
            uc=self.user
        )
    
    def test_creacion_procedimiento(self):
        """Verificar creación de procedimiento"""
        self.assertEqual(self.procedimiento.codigo, 'RES-OBT001')
        self.assertEqual(self.procedimiento.categoria, 'RESTAURATIVA')
        self.assertTrue(self.procedimiento.estado)
        self.assertEqual(
            str(self.procedimiento),
            'RES-OBT001 - Obturación con Resina'
        )
    
    def test_codigo_unico(self):
        """Verificar que el código es único"""
        with self.assertRaises(Exception):
            ProcedimientoOdontologico.objects.create(
                codigo='RES-OBT001',  # Código duplicado
                nombre='Otro procedimiento',
                categoria='RESTAURATIVA',
                duracion_estimada=30,
                uc=self.user
            )
    
    def test_categorias_validas(self):
        """Verificar categorías válidas de procedimientos"""
        categorias = [
            'DIAGNOSTICO', 'PREVENTIVA', 'RESTAURATIVA',
            'ENDODONCIA', 'PERIODONCIA', 'CIRUGIA',
            'PROSTODONCIA', 'IMPLANTES', 'ORTODONCIA',
            'URGENCIAS', 'OTROS'
        ]
        
        for i, categoria in enumerate(categorias):
            proc = ProcedimientoOdontologico.objects.create(
                codigo=f'TEST-{i:03d}',
                nombre=f'Procedimiento {categoria}',
                categoria=categoria,
                duracion_estimada=30,
                uc=self.user
            )
            self.assertEqual(proc.categoria, categoria)
    
    def test_duracion_minima(self):
        """Verificar que duración mínima es 5 minutos"""
        with self.assertRaises(ValidationError):
            proc = ProcedimientoOdontologico(
                codigo='TEST-DUR',
                nombre='Duración inválida',
                categoria='DIAGNOSTICO',
                duracion_estimada=2,  # Menor a 5
                uc=self.user
            )
            proc.full_clean()  # Dispara validación
    
    def test_campos_booleanos_por_defecto(self):
        """Verificar valores por defecto de campos booleanos"""
        proc = ProcedimientoOdontologico.objects.create(
            codigo='TEST-BOOL',
            nombre='Test Booleanos',
            categoria='DIAGNOSTICO',
            duracion_estimada=15,
            uc=self.user
            # No especificar requiere_anestesia ni afecta_odontograma
        )
        
        self.assertFalse(proc.requiere_anestesia)  # Default False
        self.assertTrue(proc.afecta_odontograma)   # Default True
        self.assertTrue(proc.estado)                # Default True
    
    def test_desactivar_procedimiento(self):
        """Verificar desactivación de procedimiento"""
        self.assertTrue(self.procedimiento.estado)
        
        self.procedimiento.estado = False
        self.procedimiento.save()
        
        proc_actualizado = ProcedimientoOdontologico.objects.get(
            pk=self.procedimiento.pk
        )
        self.assertFalse(proc_actualizado.estado)
    
    def test_campos_auditoria(self):
        """Verificar campos de auditoría"""
        self.assertIsNotNone(self.procedimiento.fc)  # Fecha creación
        self.assertIsNotNone(self.procedimiento.fm)  # Fecha modificación
        self.assertEqual(self.procedimiento.uc, self.user)  # Usuario creación
    
    def test_get_precio_para_clinica_sin_precio(self):
        """Verificar get_precio_para_clinica cuando no hay precio"""
        clinica = Clinica.objects.create(
            nombre='Clínica Test',
            ruc='1234567890001',
            telefono='0999999999',
            email='test@clinica.com',
            uc=self.user
        )
        
        precio = self.procedimiento.get_precio_para_clinica(clinica)
        self.assertIsNone(precio)


class ClinicaProcedimientoTestCase(TestCase):
    """Pruebas para el modelo ClinicaProcedimiento (precios)"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.clinica1 = Clinica.objects.create(
            nombre='Clínica A',
            ruc='1234567890001',
            telefono='0999999999',
            email='clinicaA@test.com',
            uc=self.user
        )
        
        self.clinica2 = Clinica.objects.create(
            nombre='Clínica B',
            ruc='0987654321001',
            telefono='0988888888',
            email='clinicaB@test.com',
            uc=self.user
        )
        
        self.procedimiento = ProcedimientoOdontologico.objects.create(
            codigo='RES-OBT001',
            nombre='Obturación con Resina',
            categoria='RESTAURATIVA',
            duracion_estimada=45,
            uc=self.user
        )
        
        self.precio_clinica1 = ClinicaProcedimiento.objects.create(
            clinica=self.clinica1,
            procedimiento=self.procedimiento,
            precio=Decimal('50.00'),
            moneda='USD',
            descuento_porcentaje=Decimal('0.00'),
            activo=True,
            uc=self.user
        )
    
    def test_creacion_precio_procedimiento(self):
        """Verificar creación de precio"""
        self.assertEqual(self.precio_clinica1.clinica, self.clinica1)
        self.assertEqual(self.precio_clinica1.procedimiento, self.procedimiento)
        self.assertEqual(self.precio_clinica1.precio, Decimal('50.00'))
        self.assertEqual(self.precio_clinica1.moneda, 'USD')
        self.assertTrue(self.precio_clinica1.activo)
    
    def test_unique_together_clinica_procedimiento(self):
        """Verificar que no puede haber duplicados clínica-procedimiento"""
        with self.assertRaises(Exception):
            ClinicaProcedimiento.objects.create(
                clinica=self.clinica1,  # Misma clínica
                procedimiento=self.procedimiento,  # Mismo procedimiento
                precio=Decimal('60.00'),
                uc=self.user
            )
    
    def test_diferentes_clinicas_diferentes_precios(self):
        """Verificar que diferentes clínicas pueden tener diferentes precios"""
        precio_clinica2 = ClinicaProcedimiento.objects.create(
            clinica=self.clinica2,  # Diferente clínica
            procedimiento=self.procedimiento,
            precio=Decimal('75.00'),  # Diferente precio
            moneda='USD',
            uc=self.user
        )
        
        # Verificar que ambos existen
        self.assertEqual(
            ClinicaProcedimiento.objects.filter(
                procedimiento=self.procedimiento
            ).count(),
            2
        )
        
        # Verificar precios diferentes
        self.assertNotEqual(
            self.precio_clinica1.precio,
            precio_clinica2.precio
        )
    
    def test_precio_minimo_cero(self):
        """Verificar que el precio mínimo es 0"""
        with self.assertRaises(ValidationError):
            precio = ClinicaProcedimiento(
                clinica=self.clinica2,
                procedimiento=self.procedimiento,
                precio=Decimal('-10.00'),  # Precio negativo
                uc=self.user
            )
            precio.full_clean()
    
    def test_descuento_porcentaje_valido(self):
        """Verificar validación de descuento porcentaje (0-100)"""
        # Descuento válido
        precio = ClinicaProcedimiento.objects.create(
            clinica=self.clinica2,
            procedimiento=self.procedimiento,
            precio=Decimal('100.00'),
            descuento_porcentaje=Decimal('15.50'),
            uc=self.user
        )
        self.assertEqual(precio.descuento_porcentaje, Decimal('15.50'))
        
        # Descuento inválido (> 100)
        with self.assertRaises(ValidationError):
            precio_invalido = ClinicaProcedimiento(
                clinica=self.clinica1,
                procedimiento=ProcedimientoOdontologico.objects.create(
                    codigo='TEST-DESC',
                    nombre='Test Descuento',
                    categoria='DIAGNOSTICO',
                    duracion_estimada=15,
                    uc=self.user
                ),
                precio=Decimal('100.00'),
                descuento_porcentaje=Decimal('150.00'),  # Mayor a 100
                uc=self.user
            )
            precio_invalido.full_clean()
    
    def test_get_precio_para_clinica_con_precio(self):
        """Verificar obtención de precio para clínica específica"""
        precio = self.procedimiento.get_precio_para_clinica(self.clinica1)
        self.assertEqual(precio, Decimal('50.00'))
    
    def test_moneda_por_defecto(self):
        """Verificar moneda por defecto USD"""
        precio = ClinicaProcedimiento.objects.create(
            clinica=self.clinica2,
            procedimiento=self.procedimiento,
            precio=Decimal('100.00'),
            uc=self.user
            # No especificar moneda
        )
        self.assertEqual(precio.moneda, 'USD')
    
    def test_desactivar_precio(self):
        """Verificar desactivación de precio"""
        self.assertTrue(self.precio_clinica1.activo)
        
        self.precio_clinica1.activo = False
        self.precio_clinica1.save()
        
        precio_actualizado = ClinicaProcedimiento.objects.get(
            pk=self.precio_clinica1.pk
        )
        self.assertFalse(precio_actualizado.activo)
    
    def test_notas_opcionales(self):
        """Verificar que las notas son opcionales"""
        precio = ClinicaProcedimiento.objects.create(
            clinica=self.clinica2,
            procedimiento=self.procedimiento,
            precio=Decimal('80.00'),
            uc=self.user
            # Sin notas
        )
        self.assertEqual(precio.notas, '')
        
        # Con notas
        precio.notas = 'Precio especial para convenio'
        precio.save()
        
        precio_actualizado = ClinicaProcedimiento.objects.get(pk=precio.pk)
        self.assertEqual(
            precio_actualizado.notas,
            'Precio especial para convenio'
        )


class ProcedimientosCasoUsoRealTestCase(TestCase):
    """Pruebas de casos de uso reales del sistema de procedimientos"""
    
    def setUp(self):
        """Configuración para casos de uso"""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Dos clínicas con diferentes políticas de precios
        self.clinica_economica = Clinica.objects.create(
            nombre='Clínica Económica',
            ruc='1111111111001',
            telefono='0999111111',
            email='economica@test.com',
            uc=self.user
        )
        
        self.clinica_premium = Clinica.objects.create(
            nombre='Clínica Premium',
            ruc='2222222222001',
            telefono='0999222222',
            email='premium@test.com',
            uc=self.user
        )
        
        # Procedimientos comunes
        self.limpieza = ProcedimientoOdontologico.objects.create(
            codigo='PRE-LIM001',
            codigo_cdt='D1110',
            nombre='Limpieza Dental',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            requiere_anestesia=False,
            uc=self.user
        )
        
        self.obturacion = ProcedimientoOdontologico.objects.create(
            codigo='RES-OBT001',
            codigo_cdt='D2140',
            nombre='Obturación con Resina',
            categoria='RESTAURATIVA',
            duracion_estimada=45,
            requiere_anestesia=True,
            uc=self.user
        )
        
        self.endodoncia = ProcedimientoOdontologico.objects.create(
            codigo='END-TRA001',
            codigo_cdt='D3310',
            nombre='Tratamiento de Conducto',
            categoria='ENDODONCIA',
            duracion_estimada=90,
            requiere_anestesia=True,
            uc=self.user
        )
    
    def test_caso_clinica_economica(self):
        """Clínica económica con precios bajos"""
        # Precios económicos
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_economica,
            procedimiento=self.limpieza,
            precio=Decimal('25.00'),
            uc=self.user
        )
        
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_economica,
            procedimiento=self.obturacion,
            precio=Decimal('40.00'),
            uc=self.user
        )
        
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_economica,
            procedimiento=self.endodoncia,
            precio=Decimal('100.00'),
            uc=self.user
        )
        
        # Verificar precios
        self.assertEqual(
            self.limpieza.get_precio_para_clinica(self.clinica_economica),
            Decimal('25.00')
        )
        self.assertEqual(
            self.obturacion.get_precio_para_clinica(self.clinica_economica),
            Decimal('40.00')
        )
        self.assertEqual(
            self.endodoncia.get_precio_para_clinica(self.clinica_economica),
            Decimal('100.00')
        )
    
    def test_caso_clinica_premium(self):
        """Clínica premium con precios altos"""
        # Precios premium
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_premium,
            procedimiento=self.limpieza,
            precio=Decimal('60.00'),
            uc=self.user
        )
        
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_premium,
            procedimiento=self.obturacion,
            precio=Decimal('90.00'),
            uc=self.user
        )
        
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica_premium,
            procedimiento=self.endodoncia,
            precio=Decimal('250.00'),
            uc=self.user
        )
        
        # Verificar precios
        self.assertEqual(
            self.limpieza.get_precio_para_clinica(self.clinica_premium),
            Decimal('60.00')
        )
        self.assertEqual(
            self.obturacion.get_precio_para_clinica(self.clinica_premium),
            Decimal('90.00')
        )
        self.assertEqual(
            self.endodoncia.get_precio_para_clinica(self.clinica_premium),
            Decimal('250.00')
        )
    
    def test_caso_descuento_especial(self):
        """Aplicar descuento especial a procedimiento"""
        precio_con_descuento = ClinicaProcedimiento.objects.create(
            clinica=self.clinica_premium,
            procedimiento=self.limpieza,
            precio=Decimal('60.00'),
            descuento_porcentaje=Decimal('20.00'),  # 20% descuento
            notas='Promoción mes de la salud',
            uc=self.user
        )
        
        self.assertEqual(precio_con_descuento.precio, Decimal('60.00'))
        self.assertEqual(
            precio_con_descuento.descuento_porcentaje,
            Decimal('20.00')
        )
        
        # Precio final sería: 60 - (60 * 0.20) = 48
        # (esto se calcularía en la lógica de negocio)
    
    def test_caso_procedimiento_sin_precio_en_clinica(self):
        """Verificar procedimiento que no tiene precio en clínica"""
        # No crear precio para limpieza en clínica económica
        
        precio = self.limpieza.get_precio_para_clinica(
            self.clinica_economica
        )
        
        self.assertIsNone(precio)
    
    def test_caso_multiples_procedimientos_categorias(self):
        """Verificar organización de procedimientos por categoría"""
        # Procedimientos preventivos
        preventivos = ProcedimientoOdontologico.objects.filter(
            categoria='PREVENTIVA',
            estado=True
        )
        self.assertEqual(preventivos.count(), 1)
        
        # Procedimientos restaurativos
        restaurativos = ProcedimientoOdontologico.objects.filter(
            categoria='RESTAURATIVA',
            estado=True
        )
        self.assertEqual(restaurativos.count(), 1)
        
        # Endodoncia
        endodoncias = ProcedimientoOdontologico.objects.filter(
            categoria='ENDODONCIA',
            estado=True
        )
        self.assertEqual(endodoncias.count(), 1)


class ProcedimientoIndexesTestCase(TestCase):
    """Pruebas para verificar índices de base de datos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            ruc='1234567890001',
            telefono='0999999999',
            email='test@clinica.com',
            uc=self.user
        )
    
    def test_query_por_categoria_y_estado(self):
        """Verificar query optimizado por categoría y estado"""
        # Crear varios procedimientos
        for i in range(5):
            ProcedimientoOdontologico.objects.create(
                codigo=f'RES-{i:03d}',
                nombre=f'Restauración {i}',
                categoria='RESTAURATIVA',
                duracion_estimada=30,
                estado=True,
                uc=self.user
            )
        
        # Query optimizado (usa índice)
        restaurativas_activas = ProcedimientoOdontologico.objects.filter(
            categoria='RESTAURATIVA',
            estado=True
        )
        
        self.assertEqual(restaurativas_activas.count(), 5)
    
    def test_query_precios_por_clinica_activos(self):
        """Verificar query optimizado de precios por clínica"""
        proc = ProcedimientoOdontologico.objects.create(
            codigo='TEST-001',
            nombre='Test',
            categoria='DIAGNOSTICO',
            duracion_estimada=15,
            uc=self.user
        )
        
        # Crear precios
        for i in range(3):
            ClinicaProcedimiento.objects.create(
                clinica=self.clinica,
                procedimiento=ProcedimientoOdontologico.objects.create(
                    codigo=f'PROC-{i:03d}',
                    nombre=f'Procedimiento {i}',
                    categoria='DIAGNOSTICO',
                    duracion_estimada=15,
                    uc=self.user
                ),
                precio=Decimal('50.00'),
                activo=True,
                uc=self.user
            )
        
        # Query optimizado (usa índice clinica + activo)
        precios_activos = ClinicaProcedimiento.objects.filter(
            clinica=self.clinica,
            activo=True
        )
        
        self.assertEqual(precios_activos.count(), 3)
