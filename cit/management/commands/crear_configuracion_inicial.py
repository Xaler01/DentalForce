"""
Comando para crear configuración inicial de la clínica.
Ejecutar: python manage.py crear_configuracion_inicial
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cit.models import ConfiguracionClinica, Sucursal


class Command(BaseCommand):
    help = 'Crea la configuración inicial de la clínica si no existe'

    def handle(self, *args, **kwargs):
        # Obtener la primera sucursal
        sucursal = Sucursal.objects.filter(estado=True).first()
        
        if not sucursal:
            self.stdout.write(
                self.style.ERROR('❌ No hay sucursales activas. Crea una sucursal primero.')
            )
            return
        
        # Verificar si ya existe configuración para esta sucursal
        if ConfiguracionClinica.objects.filter(sucursal=sucursal).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️  Ya existe configuración para {sucursal.nombre}')
            )
            return
        
        # Obtener usuario admin para auditoría
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        
        # Crear configuración
        config = ConfiguracionClinica.objects.create(
            sucursal=sucursal,
            horario_inicio='08:30:00',
            horario_fin='18:00:00',
            duracion_slot=30,
            atiende_lunes=True,
            atiende_martes=True,
            atiende_miercoles=True,
            atiende_jueves=True,
            atiende_viernes=True,
            atiende_sabado=True,
            atiende_domingo=False,
            sabado_hora_inicio='08:30:00',
            sabado_hora_fin='12:00:00',
            permitir_citas_mismo_dia=True,
            horas_anticipacion_minima=0,
            estado=True,
            uc=admin_user,
            um=admin_user.id
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Configuración creada para {sucursal.nombre}')
        )
        self.stdout.write(f'   📅 Horario: {config.horario_inicio} - {config.horario_fin}')
        self.stdout.write(f'   ⏱️  Slot: {config.duracion_slot} minutos')
        self.stdout.write(f'   📆 Sábados: {config.sabado_hora_inicio} - {config.sabado_hora_fin}')
        self.stdout.write(f'   🕐 Mismo día: {"✅ Sí" if config.permitir_citas_mismo_dia else "❌ No"}')
