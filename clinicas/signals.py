"""
Signals para auto-creación de usuarios en PowerDent

Cuando se crea una Clínica → Se crea automáticamente un Admin de Clínica
Cuando se crea una Sucursal → Se crean automáticamente Auxiliar + Dentista
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from clinicas.models import Clinica, Sucursal
from usuarios.models import UsuarioClinica, RolUsuario
from usuarios.utils import (
    generar_password_temporal,
    generar_username_unico,
    generar_email_temporal,
    enviar_credenciales_email
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Clinica)
def crear_admin_clinica(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta al crear una nueva Clínica.
    
    Crea automáticamente:
    - Usuario tipo ADMIN_CLINICA
    - Username: admin_{clinica_id}_{clinica_nombre_slug}
    - Password temporal
    - Envía credenciales por email (si está configurado)
    
    Args:
        sender: Model class (Clinica)
        instance: Instancia de Clinica creada
        created: Boolean indicando si es creación o actualización
        **kwargs: Argumentos adicionales
    """
    if created:
        try:
            # Generar datos del usuario
            username = generar_username_unico('admin', instance.id, instance.nombre)
            password_temporal = generar_password_temporal()
            email = instance.email if instance.email else generar_email_temporal(username)
            
            # Verificar si ya existe el username (por si acaso)
            if User.objects.filter(username=username).exists():
                username = f"{username}_{instance.id}"
                logger.warning(f"Username duplicado detectado. Usando: {username}")
            
            # Crear usuario de Django
            admin_user = User.objects.create_user(
                username=username,
                email=email,
                password=password_temporal,
                first_name='Admin',
                last_name=instance.nombre[:50],  # Limitar a 50 chars
                is_staff=False,  # No es admin de Django
                is_active=True
            )
            
            # Crear asociación con clínica
            UsuarioClinica.objects.create(
                usuario=admin_user,
                clinica=instance,
                sucursal=None,  # Admin de clínica no tiene sucursal específica
                rol=RolUsuario.ADMIN_CLINICA,
                activo=True
            )
            
            # Enviar credenciales por email
            enviar_credenciales_email(admin_user, password_temporal, 'admin_clinica')
            
            logger.info(f"✅ Admin de clínica creado automáticamente: {username} para {instance.nombre}")
            
        except Exception as e:
            logger.error(f"❌ Error al crear admin de clínica para {instance.nombre}: {str(e)}")
            raise


@receiver(post_save, sender=Sucursal)
def crear_usuarios_sucursal(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta al crear una nueva Sucursal.
    
    Crea automáticamente:
    - 1 Usuario AUXILIAR asignado a la sucursal
    - 1 Usuario DENTISTA asignado a la sucursal
    - Passwords temporales para ambos
    - Envía credenciales por email (si está configurado)
    
    Args:
        sender: Model class (Sucursal)
        instance: Instancia de Sucursal creada
        created: Boolean indicando si es creación o actualización
        **kwargs: Argumentos adicionales
    """
    if created:
        try:
            # ==========================================
            # CREAR AUXILIAR
            # ==========================================
            username_aux = generar_username_unico('aux', instance.id, instance.nombre)
            password_aux = generar_password_temporal()
            email_aux = instance.email if instance.email else generar_email_temporal(username_aux)
            
            # Verificar unicidad del username
            if User.objects.filter(username=username_aux).exists():
                username_aux = f"{username_aux}_{instance.id}"
            
            # Crear usuario auxiliar
            auxiliar_user = User.objects.create_user(
                username=username_aux,
                email=email_aux,
                password=password_aux,
                first_name='Auxiliar',
                last_name=instance.nombre[:50],
                is_staff=False,
                is_active=True
            )
            
            # Crear asociación con clínica y sucursal
            UsuarioClinica.objects.create(
                usuario=auxiliar_user,
                clinica=instance.clinica,
                sucursal=instance,
                rol=RolUsuario.AUXILIAR,
                activo=True
            )
            
            # Enviar credenciales
            enviar_credenciales_email(auxiliar_user, password_aux, 'auxiliar')
            
            logger.info(f"✅ Auxiliar creado automáticamente: {username_aux} para sucursal {instance.nombre}")
            
            # ==========================================
            # CREAR DENTISTA
            # ==========================================
            username_dent = generar_username_unico('dent', instance.id, instance.nombre)
            password_dent = generar_password_temporal()
            email_dent = generar_email_temporal(username_dent)
            
            # Verificar unicidad del username
            if User.objects.filter(username=username_dent).exists():
                username_dent = f"{username_dent}_{instance.id}"
            
            # Crear usuario dentista
            dentista_user = User.objects.create_user(
                username=username_dent,
                email=email_dent,
                password=password_dent,
                first_name='Dentista',
                last_name=instance.nombre[:50],
                is_staff=False,
                is_active=True
            )
            
            # Crear asociación con clínica y sucursal
            UsuarioClinica.objects.create(
                usuario=dentista_user,
                clinica=instance.clinica,
                sucursal=instance,
                rol=RolUsuario.DENTISTA,
                activo=True
            )
            
            # Enviar credenciales
            enviar_credenciales_email(dentista_user, password_dent, 'dentista')
            
            logger.info(f"✅ Dentista creado automáticamente: {username_dent} para sucursal {instance.nombre}")
            
        except Exception as e:
            logger.error(f"❌ Error al crear usuarios para sucursal {instance.nombre}: {str(e)}")
            raise
