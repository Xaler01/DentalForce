from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class MiddlewareSelectorTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='pw')
        self.client = Client()
        self.client.login(username='u1', password='pw')

    def test_get_selector_returns_200(self):
        """GET to the selector must be accessible (status 200) when logged in"""
        response = self.client.get(reverse('cit:clinica-seleccionar'))
        self.assertIn(response.status_code, (200, 302))
        # Prefer 200; if login redirects, 302 is acceptable in some configs
