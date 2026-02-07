import secrets
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from clinicas.models import Clinica
from usuarios.models import UsuarioClinica, RolUsuario


class Command(BaseCommand):
    """
    Comando para crear rápidamente un administrador de clínica.
    
    Uso:
        python manage.py create_clinic_admin --clinica="Tio Alex" \
            --email=admin@example.com --nombre="Juan Admin"
    """
    
    help = 'Crear un administrador de clínica rápidamente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clinica',
            type=str,
            required=True,
            help='Nombre de la clínica (debe existir en el sistema)'
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email del nuevo administrador (debe ser único)'
        )
        parser.add_argument(
            '--nombre',
            type=str,
            required=True,
            help='Nombre completo del administrador'
        )
    
    def handle(self, *args, **options):
        clinica_nombre = options['clinica']
        email = options['email']
        nombre_completo = options['nombre']
        
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('CREAR ADMINISTRADOR DE CLÍNICA'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        # 1. Validar que clínica existe
        try:
            clinica = Clinica.objects.get(nombre__iexact=clinica_nombre)
            self.stdout.write(f"✅ Clínica encontrada: {clinica.nombre}")
        except Clinica.DoesNotExist:
            raise CommandError(
                f"❌ Clínica no encontrada: '{clinica_nombre}'\n"
                f"   Clínicas disponibles: {', '.join(Clinica.objects.values_list('nombre', flat=True))}"
            )
        
        # 2. Validar que email es único
        if User.objects.filter(email=email).exists():
            raise CommandError(
                f"❌ Email ya existe en el sistema: {email}"
            )
        
        # 3. Validar nombre no vacío
        if not nombre_completo or len(nombre_completo.strip()) < 3:
            raise CommandError(
                f"❌ Nombre incompleto. Se requiere mínimo 3 caracteres."
            )
        
        # 4. Generar contraseña temporal
        password_temporal = secrets.token_urlsafe(12)
        
        # 5. Crear User
        try:
            # Separar nombre y apellido (último espacio)
            partes = nombre_completo.rsplit(' ', 1)
            first_name = partes[0]
            last_name = partes[1] if len(partes) > 1 else ''
            
            usuario = User.objects.create_user(
                username=email.split('@')[0],  # Username derivado del email
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,  # No es staff (usa UsuarioClinica para permisos)
                is_superuser=False
            )
            usuario.set_password(password_temporal)
            usuario.save()
            self.stdout.write(f"✅ Usuario Django creado: {usuario.email}")
        except Exception as e:
            raise CommandError(f"❌ Error al crear usuario Django: {e}")
        
        # 6. Crear UsuarioClinica con rol ADMIN_CLINICA
        try:
            usuario_clinica = UsuarioClinica.objects.create(
                usuario=usuario,
                clinica=clinica,
                rol=RolUsuario.ADMIN_CLINICA,
                activo=True
            )
            self.stdout.write(f"✅ UsuarioClinica creado: {usuario_clinica}")
        except Exception as e:
            # Rollback: eliminar usuario si falla la creación de UsuarioClinica
            usuario.delete()
            raise CommandError(f"❌ Error al crear asignación de clínica: {e}")
        
        # 7. Mostrar credenciales
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('✅ ADMINISTRADOR CREADO EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS(f"\n📋 CREDENCIALES:\n"))
        self.stdout.write(f"   Email:       {email}")
        self.stdout.write(f"   Contraseña:  {password_temporal}")
        self.stdout.write(f"   Clínica:     {clinica.nombre}")
        self.stdout.write(f"   Rol:         {usuario_clinica.get_rol_display()}")
        self.stdout.write(f"\n🔗 URL de login:")
        self.stdout.write(f"   http://localhost:8000/accounts/login/")
        self.stdout.write(f"\n⚠️  IMPORTANTE:")
        self.stdout.write(f"   - Comparta estas credenciales de forma segura")
        self.stdout.write(f"   - El usuario debe cambiar su contraseña en el primer login")
        self.stdout.write(f"   - El rol '{usuario_clinica.get_rol_display()}' tiene acceso completo a la clínica")
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))
