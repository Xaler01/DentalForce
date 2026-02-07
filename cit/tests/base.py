"""
Base test classes para tests que requieren contexto multi-tenant
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from cit.models import Clinica


class MultiTenantTestCase(TestCase):
    """
    Base class para tests que necesitan contexto multi-tenant con clinica_id en sesión.
    Automáticamente crea una clínica de prueba y setea clinica_id en la sesión.
    """
    
    def setUp(self):
        """Configuración base de multi-tenant"""
        self.client = Client()
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        
        # Crear clínica de prueba
        self.clinica = Clinica.objects.create(
            nombre='Clinica Test',
            ruc='1234567890001',
            direccion='Dir test',
            telefono='0999999999',
            email='clinic@test.com',
            estado=True,
            uc=self.user,
            um=self.user.id,
        )
        
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Set clinica_id en sesión
        session = self.client.session
        session['clinica_id'] = self.clinica.id
        session.save()
    
    def _set_clinica_in_session(self, clinica):
        """Utility para cambiar clinica_id en sesión (útil para tests multi-clínica)"""
        session = self.client.session
        session['clinica_id'] = clinica.id
        session.save()
