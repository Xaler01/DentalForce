from django.apps import AppConfig


class CitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cit'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import cit.signals
