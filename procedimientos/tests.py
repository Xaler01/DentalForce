"""
Tests para el catálogo de procedimientos odontológicos.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from clinicas.models import Clinica
from procedimientos.models import ProcedimientoOdontologico, ClinicaProcedimiento


class ProcedimientoOdontologicoTestCase(TestCase):
    """Tests para el modelo ProcedimientoOdontologico."""
    
    @classmethod
    def setUpClass(cls):
        """Setup una vez para toda la clase."""
        super().setUpClass()
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass'
        )
    
    def test_crear_procedimiento(self):
        """Verificar que se puede crear un procedimiento."""
        proc = ProcedimientoOdontologico.objects.create(
            codigo='TEST-001',
            nombre='Procedimiento de Prueba',
            categoria='DIAGNOSTICO',
            duracion_estimada=30,
            uc=self.admin_user
        )
        self.assertEqual(proc.codigo, 'TEST-001')
        self.assertEqual(proc.nombre, 'Procedimiento de Prueba')
        self.assertTrue(proc.estado)
    
    def test_codigo_unico(self):
        """Verificar que el código es único."""
        ProcedimientoOdontologico.objects.create(
            codigo='UNICO-001',
            nombre='Procedimiento 1',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            uc=self.admin_user
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProcedimientoOdontologico.objects.create(
                codigo='UNICO-001',
                nombre='Procedimiento 2',
                categoria='PREVENTIVA',
                duracion_estimada=30,
                uc=self.admin_user
            )
    
    def test_categorias_validas(self):
        """Verificar que las categorías son válidas."""
        categorias_validas = [
            'DIAGNOSTICO', 'PREVENTIVA', 'RESTAURATIVA', 'ENDODONCIA',
            'PERIODONCIA', 'CIRUGIA', 'PROSTODONCIA', 'IMPLANTES',
            'ORTODONCIA', 'URGENCIAS', 'OTROS'
        ]
        
        for categoria in categorias_validas:
            proc = ProcedimientoOdontologico.objects.create(
                codigo=f'CAT-{categoria}',
                nombre=f'Test {categoria}',
                categoria=categoria,
                duracion_estimada=30,
                uc=self.admin_user
            )
            self.assertEqual(proc.categoria, categoria)
    
    def test_duracion_minima(self):
        """Verificar que la duración mínima es 5 minutos."""
        from django.core.exceptions import ValidationError
        
        proc = ProcedimientoOdontologico(
            codigo='DUR-001',
            nombre='Duracion Minima',
            categoria='DIAGNOSTICO',
            duracion_estimada=4,  # Menos de 5
            uc=self.admin_user
        )
        
        with self.assertRaises(ValidationError):
            proc.full_clean()
    
    def test_str_representation(self):
        """Verificar la representación en string."""
        proc = ProcedimientoOdontologico.objects.create(
            codigo='STR-001',
            nombre='Procedimiento String',
            categoria='DIAGNOSTICO',
            duracion_estimada=30,
            uc=self.admin_user
        )
        
        expected_str = 'STR-001 - Procedimiento String'
        self.assertEqual(str(proc), expected_str)
    
    def test_get_precio_para_clinica(self):
        """Verificar obtención de precio para clínica específica."""
        proc = ProcedimientoOdontologico.objects.create(
            codigo='PREC-001',
            nombre='Con Precio',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            uc=self.admin_user
        )
        
        # Sin precio definido
        clinica = Clinica.objects.create(
            nombre='Test Clinic',
            direccion='Test Address',
            telefono='123456789',
            email='test@example.com',
            pais='EC',
            uc=self.admin_user
        )
        
        precio = proc.get_precio_para_clinica(clinica)
        self.assertIsNone(precio)
        
        # Con precio definido
        ClinicaProcedimiento.objects.create(
            clinica=clinica,
            procedimiento=proc,
            precio=50.00,
            uc=self.admin_user
        )
        
        precio = proc.get_precio_para_clinica(clinica)
        self.assertEqual(float(precio), 50.00)


class ClinicaProcedimientoTestCase(TestCase):
    """Tests para el modelo ClinicaProcedimiento."""
    
    @classmethod
    def setUpClass(cls):
        """Setup una vez para toda la clase."""
        super().setUpClass()
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass'
        )
        
        # Crear clínica de prueba
        cls.clinica = Clinica.objects.create(
            nombre='Clínica Test',
            direccion='Calle Test',
            telefono='123456789',
            email='clinica@example.com',
            pais='EC',
            moneda='USD',
            uc=cls.admin_user
        )
        
        # Crear procedimiento de prueba
        cls.procedimiento = ProcedimientoOdontologico.objects.create(
            codigo='TEST-PROC',
            nombre='Procedimiento Test',
            categoria='PREVENTIVA',
            duracion_estimada=30,
            uc=cls.admin_user
        )
    
    def test_crear_precio_procedimiento(self):
        """Verificar que se puede crear un precio para un procedimiento."""
        cp = ClinicaProcedimiento.objects.create(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            uc=self.admin_user
        )
        self.assertEqual(float(cp.precio), 100.00)
        self.assertEqual(cp.moneda, 'USD')  # Heredada de clínica
    
    def test_unicidad_clinica_procedimiento(self):
        """Verificar que no puede haber duplicados clinica-procedimiento."""
        ClinicaProcedimiento.objects.create(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            uc=self.admin_user
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ClinicaProcedimiento.objects.create(
                clinica=self.clinica,
                procedimiento=self.procedimiento,
                precio=200.00,
                uc=self.admin_user
            )
    
    def test_precio_con_descuento(self):
        """Verificar cálculo de precio con descuento."""
        cp = ClinicaProcedimiento.objects.create(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            descuento_porcentaje=20,  # 20% descuento
            uc=self.admin_user
        )
        
        # Precio final debe ser 80.00
        precio_final = cp.get_precio_con_descuento()
        self.assertEqual(float(precio_final), 80.00)
    
    def test_descuento_minimo_maximo(self):
        """Verificar límites de descuento (0-100)."""
        from django.core.exceptions import ValidationError
        
        # Descuento negativo
        cp_neg = ClinicaProcedimiento(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            descuento_porcentaje=-5,
            uc=self.admin_user
        )
        with self.assertRaises(ValidationError):
            cp_neg.full_clean()
        
        # Descuento > 100
        cp_over = ClinicaProcedimiento(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            descuento_porcentaje=150,
            uc=self.admin_user
        )
        with self.assertRaises(ValidationError):
            cp_over.full_clean()
    
    def test_str_representation(self):
        """Verificar la representación en string."""
        cp = ClinicaProcedimiento.objects.create(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=75.50,
            uc=self.admin_user
        )
        
        expected_str = f"{self.clinica.nombre} - {self.procedimiento.codigo}: $75.50"
        self.assertEqual(str(cp), expected_str)
    
    def test_herencia_moneda_de_clinica(self):
        """Verificar que hereda la moneda de la clínica."""
        cp = ClinicaProcedimiento.objects.create(
            clinica=self.clinica,
            procedimiento=self.procedimiento,
            precio=100.00,
            uc=self.admin_user
        )
        
        # Debe tener moneda USD (de la clínica)
        self.assertEqual(cp.moneda, 'USD')


class CatalogoCercanoTestCase(TestCase):
    """Tests para verificar que el catálogo está completo."""
    
    def test_catalogo_tiene_procedimientos(self):
        """Verificar que el catálogo tiene procedimientos cargados."""
        count = ProcedimientoOdontologico.objects.count()
        self.assertGreater(count, 0, "El catálogo debe tener al menos 1 procedimiento")
    
    def test_todas_las_categorias_existen(self):
        """Verificar que todas las categorías tienen procedimientos."""
        categorias = [
            'DIAGNOSTICO', 'PREVENTIVA', 'RESTAURATIVA', 'ENDODONCIA',
            'PERIODONCIA', 'CIRUGIA', 'PROSTODONCIA', 'IMPLANTES',
            'ORTODONCIA', 'URGENCIAS', 'OTROS'
        ]
        
        for categoria in categorias:
            exists = ProcedimientoOdontologico.objects.filter(categoria=categoria).exists()
            self.assertTrue(exists, f"La categoría {categoria} debe tener al menos 1 procedimiento")
    
    def test_codigos_unicos_en_catalogo(self):
        """Verificar que los códigos son únicos."""
        from django.db.models import Count
        
        duplicados = ProcedimientoOdontologico.objects.values('codigo').annotate(
            count=Count('codigo')
        ).filter(count__gt=1)
        
        self.assertEqual(len(list(duplicados)), 0, "No debe haber códigos duplicados")
