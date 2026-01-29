"""
Signals para auto-creación de usuarios en PowerDent

Cuando se crea una Clínica → Se crea automáticamente un Admin de Clínica
Cuando se crea una Sucursal → Se crean automáticamente Auxiliar + Dentista
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from clinicas.models import Clinica, Sucursal
from usuarios.models import UsuarioClinica, RolUsuario, RolUsuarioPowerDent
from usuarios.utils import (
    generar_password_temporal,
    generar_username_unico,
    generar_email_temporal,
    enviar_credenciales_email
)
import logging

logger = logging.getLogger(__name__)


def crear_comisiones_por_defecto(dentista, porcentaje_defecto=15):
    """
    Crea comisiones por defecto para un dentista en todas sus especialidades asignadas.
    
    Solo crea comisiones para las especialidades que el dentista tiene asignadas.
    Si el dentista no tiene especialidades asignadas, no crea comisiones.
    
    Args:
        dentista: Instancia de Dentista
        porcentaje_defecto: Porcentaje por defecto (default 15%)
    """
    try:
        from personal.models import ComisionDentista
        
        # Obtener especialidades asignadas al dentista y que estén activas
        especialidades = dentista.especialidades.filter(estado=True)
        
        if not especialidades.exists():
            logger.info(f"ℹ️  {dentista.usuario.username} no tiene especialidades asignadas, omitiendo comisiones")
            return
        
        for especialidad in especialidades:
            # Verificar si ya existe comisión para esta combinación
            if not ComisionDentista.objects.filter(
                dentista=dentista,
                especialidad=especialidad
            ).exists():
                ComisionDentista.objects.create(
                    dentista=dentista,
                    uc=dentista.usuario,
                    especialidad=especialidad,
                    tipo_comision='PORCENTAJE',
                    porcentaje=porcentaje_defecto,
                    activo=True
                )
        
        logger.info(f"✅ Comisiones por defecto creadas para {dentista.usuario.username} ({especialidades.count()} especialidades, 15%)")
    except Exception as e:
        logger.error(f"❌ Error al crear comisiones para {dentista.usuario.username}: {str(e)}")


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
            usuario_clinica = UsuarioClinica.objects.create(
                usuario=admin_user,
                clinica=instance,
                sucursal=None,  # Admin de clínica no tiene sucursal específica
                rol=RolUsuario.ADMIN_CLINICA,
                activo=True,
                contrasena_temporal=True  # Marcar como temporal
            )
            
            # Asignar rol granular "Administrador de Clínica" si existe
            try:
                rol_admin = RolUsuarioPowerDent.objects.filter(
                    nombre='Administrador de Clínica',
                    clinica__isnull=True,  # Rol global
                    activo=True
                ).first()
                
                if rol_admin:
                    usuario_clinica.roles_personalizados.add(rol_admin)
                    logger.info(f"✅ Rol 'Administrador de Clínica' asignado a {username}")
                else:
                    logger.warning(f"⚠️  Rol 'Administrador de Clínica' no encontrado. Ejecutar: python manage.py load_permissions")
            except Exception as e:
                logger.error(f"Error al asignar rol granular: {str(e)}")
            
            # Enviar credenciales por email a la clínica (no al usuario temporal)
            from usuarios.utils import enviar_credenciales_a_destinatario
            if instance.email:
                enviar_credenciales_a_destinatario(
                    email_destinatario=instance.email,
                    nombre_usuario=admin_user.username,
                    password_temporal=password_temporal,
                    tipo_usuario='admin_clinica',
                    clinica_nombre=instance.nombre
                )
            else:
                logger.warning(f"⚠️  No hay email de clínica para enviar credenciales. Clínica: {instance.nombre}")
            
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
                activo=True,
                contrasena_temporal=True  # Marcar como temporal
            )

            # Crear perfil de Personal (administrativo/auxiliar)
            from personal.models import Personal
            personal = Personal.objects.create(
                usuario=auxiliar_user,
                uc=auxiliar_user,
                tipo_personal='auxiliar',
                tipo_compensacion='MENSUAL',
                salario_mensual=482,
                sucursal_principal=instance,
                estado=True
            )
            personal.sucursales.add(instance)
            
            # Enviar credenciales al admin de la clínica (no al usuario temporal creado)
            from usuarios.utils import enviar_credenciales_a_destinatario
            if instance.clinica.email:
                enviar_credenciales_a_destinatario(
                    email_destinatario=instance.clinica.email,
                    nombre_usuario=username_aux,
                    password_temporal=password_aux,
                    tipo_usuario='auxiliar',
                    clinica_nombre=instance.clinica.nombre,
                    sucursal_nombre=instance.nombre
                )
            else:
                logger.warning(f"⚠️  No hay email de clínica para enviar credenciales. Clínica: {instance.clinica.nombre}")
            
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
                activo=True,
                contrasena_temporal=True  # Marcar como temporal
            )
            
            # Crear perfil profesional de Dentista
            from personal.models import Dentista
            dentista = Dentista.objects.create(
                usuario=dentista_user,
                uc=dentista_user,  # Usuario que crea el registro
                sucursal_principal=instance,
                cedula_profesional=None,  # Se puede actualizar después
                telefono_movil=None,  # Se puede actualizar después
                estado=True
            )
            # Las especialidades se pueden asignar después por el administrador
            
            # Crear horarios por defecto basados en la configuración de la clínica
            try:
                from cit.models import ConfiguracionClinica
                from personal.models import DisponibilidadDentista
                from datetime import datetime
                
                config = ConfiguracionClinica.objects.filter(estado=True).first()
                
                if config:
                    # Obtener días y horarios de la clínica
                    dias_atiende = config.get_dias_atencion()
                    for dia in dias_atiende:
                        horario = config.get_horario_dia(dia)
                        if horario:
                            DisponibilidadDentista.objects.create(
                                dentista=dentista,
                                uc=dentista_user,
                                sucursal=instance,
                                dia_semana=dia,
                                hora_inicio=horario[0],
                                hora_fin=horario[1],
                                activo=True
                            )
                else:
                    # Si no hay configuración de clínica, usar horario por defecto (8:30-18:00 L-V)
                    default_inicio = datetime.strptime('08:30', '%H:%M').time()
                    default_fin = datetime.strptime('18:00', '%H:%M').time()
                    for dia in range(5):  # Lunes a Viernes
                        DisponibilidadDentista.objects.create(
                            dentista=dentista,
                            uc=dentista_user,
                            sucursal=instance,
                            dia_semana=dia,
                            hora_inicio=default_inicio,
                            hora_fin=default_fin,
                            activo=True
                        )
                
                logger.info(f"✅ Horarios por defecto creados para dentista {username_dent}")
            except Exception as e:
                logger.error(f"❌ Error al crear horarios para dentista {username_dent}: {str(e)}")
            
            # Crear comisiones por defecto (15%)
            crear_comisiones_por_defecto(dentista, porcentaje_defecto=15)
            
            # Enviar credenciales al admin de la clínica (no al usuario temporal creado)
            if instance.clinica.email:
                enviar_credenciales_a_destinatario(
                    email_destinatario=instance.clinica.email,
                    nombre_usuario=username_dent,
                    password_temporal=password_dent,
                    tipo_usuario='dentista',
                    clinica_nombre=instance.clinica.nombre,
                    sucursal_nombre=instance.nombre
                )
            else:
                logger.warning(f"⚠️  No hay email de clínica para enviar credenciales. Clínica: {instance.clinica.nombre}")
            
            logger.info(f"✅ Dentista creado automáticamente: {username_dent} para sucursal {instance.nombre}")
            
        except Exception as e:
            logger.error(f"❌ Error al crear usuarios para sucursal {instance.nombre}: {str(e)}")
            raise
