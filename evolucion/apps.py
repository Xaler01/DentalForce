from django.apps import AppConfig


class EvolucionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evolucion'
    
    def ready(self):
        """Importar señales cuando la app esté lista"""
        import evolucion.signals  # noqa

