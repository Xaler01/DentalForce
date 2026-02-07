"""
Management command para configurar Odontólogos Directores en clínicas nuevas.

Uso:
    # 1. Crear el rol "Odontólogo Director" globalmente
    python manage.py setup_odontolog_director --create-role
    
    # 2. Asignar el rol a un usuario existente
    python manage.py setup_odontolog_director --user dr_garcia --clinica "Clínica Orbedent" --add-role "Odontólogo Director"
    
    # 3. Ver configuración de permisos
    python manage.py setup_odontolog_director --list-permisos "Odontólogo Director"
    
    # 4. Listar roles disponibles
    python manage.py setup_odontolog_director --list-roles
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from usuarios.models import RolUsuarioDentalForce, PermisoPersonalizado, UsuarioClinica
from clinicas.models import Clinica


class Command(BaseCommand):
    help = 'Configura roles de Odontólogo Director para clínicas nuevas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-role',
            action='store_true',
            help='Crea el rol "Odontólogo Director" si no existe',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario a configurar',
        )
        parser.add_argument(
            '--clinica',
            type=str,
            help='Nombre de la clínica',
        )
        parser.add_argument(
            '--add-role',
            type=str,
            help='Rol a agregar al usuario (ej: "Odontólogo Director")',
        )
        parser.add_argument(
            '--list-roles',
            action='store_true',
            help='Lista todos los roles disponibles',
        )
        parser.add_argument(
            '--list-permisos',
            type=str,
            help='Lista permisos de un rol específico',
        )

    def handle(self, *args, **options):
        if options['create_role']:
            self.create_odontolog_director_role()
        elif options['list_roles']:
            self.list_roles()
        elif options['list_permisos']:
            self.list_permisos_rol(options['list_permisos'])
        elif options['user'] and options['clinica'] and options['add_role']:
            self.add_role_to_user(options['user'], options['clinica'], options['add_role'])
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Por favor, especifica una acción. Usa --help para más información.'
                )
            )

    def create_odontolog_director_role(self):
        """Crea el rol Odontólogo Director con todos los permisos necesarios"""
        self.stdout.write('Creando rol "Odontólogo Director"...\n')

        # Verificar si el rol ya existe
        rol, created = RolUsuarioDentalForce.objects.get_or_create(
            nombre='Odontólogo Director',
            clinica=None,  # Rol global
            defaults={
                'descripcion': (
                    'Para odontólogos que dirigen clínicas nuevas. '
                    'Acceso completo a: odontología, recepción, facturación e inventario básico. '
                    'Escalable: cambiar a rol "Dentista" cuando creza el equipo.'
                ),
                'activo': True
            }
        )

        if not created:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Rol "{rol.nombre}" ya existe. Actualizando permisos...')
            )

        # Permisos a asignar
        codigos_permisos = [
            # ODONTOLOGÍA (completo)
            'odontologia.crear_procedimiento',
            'odontologia.editar_diagnostico',
            'odontologia.registrar_evolucion',
            'odontologia.prescribir_medicinas',
            'odontologia.ver_radiografias',
            # RECEPCIÓN (completo)
            'recepcion.ver_citas',
            'recepcion.crear_cita',
            'recepcion.editar_cita',
            'recepcion.cancelar_cita',
            'recepcion.gestionar_pacientes',
            'recepcion.ver_historiales',
            # FACTURACIÓN (completo)
            'facturacion.ver_facturas',
            'facturacion.crear_factura',
            'facturacion.editar_factura',
            'facturacion.anular_factura',
            # INVENTARIO (básico)
            'inventario.ver_inventario',
            'inventario.solicitar_inventario',
            # REPORTES (básico)
            'reportes.ver_reportes_general',
            'reportes.ver_reportes_financiero',
        ]

        # Obtener y asignar permisos
        permisos = PermisoPersonalizado.objects.filter(codigo__in=codigos_permisos, activo=True)
        rol.permisos.set(permisos)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Rol "Odontólogo Director" configurado con {permisos.count()} permisos'
            )
        )

        # Mostrar resumen de permisos
        self.stdout.write('\n📋 Permisos asignados:')
        categorias = {}
        for permiso in permisos.order_by('categoria'):
            if permiso.categoria not in categorias:
                categorias[permiso.categoria] = []
            categorias[permiso.categoria].append(f"  ✓ {permiso.nombre}")

        for categoria, permisos_list in categorias.items():
            self.stdout.write(f'\n{categoria.upper()}:')
            for permiso in permisos_list:
                self.stdout.write(permiso)

    def add_role_to_user(self, username, clinica_name, role_name):
        """Agrega un rol a un usuario en una clínica específica"""
        try:
            usuario = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{username}" no existe')

        try:
            clinica = Clinica.objects.get(nombre=clinica_name)
        except Clinica.DoesNotExist:
            raise CommandError(f'Clínica "{clinica_name}" no existe')

        try:
            rol = RolUsuarioDentalForce.objects.get(nombre=role_name, clinica=None)
        except RolUsuarioDentalForce.DoesNotExist:
            raise CommandError(
                f'Rol "{role_name}" no existe. Usa --list-roles para ver disponibles'
            )

        try:
            usuario_clinica = UsuarioClinica.objects.get(usuario=usuario, clinica=clinica)
        except UsuarioClinica.DoesNotExist:
            raise CommandError(
                f'Usuario "{username}" no está asignado a clínica "{clinica_name}"'
            )

        # Agregar el rol
        usuario_clinica.roles_personalizados.add(rol)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Rol "{role_name}" asignado a {usuario.username} en {clinica.nombre}'
            )
        )

        # Mostrar resumen
        roles = usuario_clinica.roles_personalizados.all()
        self.stdout.write(f'\n📋 Roles actuales para {usuario.username}:')
        for r in roles:
            self.stdout.write(f'  • {r.nombre} ({r.permisos.count()} permisos)')

    def list_roles(self):
        """Lista todos los roles disponibles"""
        roles = RolUsuarioDentalForce.objects.filter(clinica=None, activo=True).order_by('nombre')

        if not roles.exists():
            self.stdout.write(self.style.WARNING('No hay roles configurados'))
            return

        self.stdout.write(self.style.SUCCESS('\n📋 ROLES DISPONIBLES:\n'))
        for i, rol in enumerate(roles, 1):
            self.stdout.write(
                f'{i}. {rol.nombre}'
                f'\n   Descripción: {rol.descripcion}'
                f'\n   Permisos: {rol.permisos.count()}\n'
            )

    def list_permisos_rol(self, nombre_rol):
        """Lista los permisos de un rol específico"""
        try:
            rol = RolUsuarioDentalForce.objects.get(nombre=nombre_rol)
        except RolUsuarioDentalForce.DoesNotExist:
            raise CommandError(f'Rol "{nombre_rol}" no existe')

        permisos = rol.permisos.all().order_by('categoria', 'nombre')

        if not permisos.exists():
            self.stdout.write(self.style.WARNING(f'Rol "{nombre_rol}" no tiene permisos asignados'))
            return

        self.stdout.write(
            self.style.SUCCESS(f'\n📋 PERMISOS DEL ROL "{nombre_rol}" ({permisos.count()}):\n')
        )

        categorias = {}
        for permiso in permisos:
            if permiso.categoria not in categorias:
                categorias[permiso.categoria] = []
            categorias[permiso.categoria].append(permiso)

        for categoria, permisos_list in categorias.items():
            self.stdout.write(self.style.WARNING(f'{categoria.upper()}:'))
            for permiso in permisos_list:
                self.stdout.write(f'  ✓ {permiso.nombre} ({permiso.codigo})')
            self.stdout.write('')
