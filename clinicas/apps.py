from django.apps import AppConfig


class ClinicasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinicas'
    verbose_name = 'Gestión de Clínicas y Sucursales'

    def ready(self):
        """
        Método que se ejecuta cuando la app está lista.
        Importa los signals para registrarlos.
        """
        import clinicas.signals  # noqa
