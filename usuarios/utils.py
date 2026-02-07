"""
Utilidades para gestión de usuarios en DentalForce
"""
import secrets
import string
from django.utils.text import slugify


def generar_password_temporal():
    """
    Genera una contraseña temporal segura de 12 caracteres.
    
    Formato: PwrDnt2026ABC123!
    - Prefijo: "PwrDnt2026"
    - 6 caracteres aleatorios (letras mayúsculas y dígitos)
    - Símbolo final: "!"
    
    Returns:
        str: Contraseña temporal
    """
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(6))
    return f"PwrDnt2026{random_part}!"


def generar_username_unico(prefijo, id_referencia, nombre):
    """
    Genera un username único y descriptivo.
    
    Args:
        prefijo (str): Prefijo del username (admin, aux, dent, recep)
        id_referencia (int): ID de la clínica o sucursal
        nombre (str): Nombre de la clínica o sucursal
    
    Returns:
        str: Username en formato {prefijo}_{id}_{nombre_slug}
    
    Ejemplos:
        >>> generar_username_unico('admin', 5, 'Clínica Norte')
        'admin_5_clinica_norte'
        >>> generar_username_unico('aux', 12, 'Sucursal Centro')
        'aux_12_sucursal_centro'
    """
    nombre_slug = slugify(nombre)[:20]  # Limitar a 20 caracteres
    username = f"{prefijo}_{id_referencia}_{nombre_slug}"
    
    # Asegurar que no sea demasiado largo (username max 150 chars)
    if len(username) > 150:
        username = username[:150]
    
    return username


def generar_email_temporal(username, dominio='dentalforce.local'):
    """
    Genera un email temporal basado en el username.
    
    Args:
        username (str): Nombre de usuario
        dominio (str): Dominio del email (default: dentalforce.local)
    
    Returns:
        str: Email en formato {username}@{dominio}
    
    Ejemplos:
        >>> generar_email_temporal('admin_5_example')
        'admin_5_example@example.local'
    """
    return f"{username}@{dominio}"


def enviar_credenciales_email(usuario, password_temporal, tipo_usuario='usuario'):
    """
    Envía las credenciales de acceso por email al nuevo usuario.
    
    Args:
        usuario (User): Instancia del usuario creado
        password_temporal (str): Contraseña temporal generada
        tipo_usuario (str): Tipo de usuario (admin_clinica, auxiliar, dentista)
    
    Returns:
        bool: True si se envió exitosamente, False en caso contrario
    
    TODO: Implementar envío real de email cuando se configure SMTP
    Por ahora, solo registra en logs.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Determinar saludo según tipo de usuario
    saludos = {
        'admin_clinica': 'Administrador de Clínica',
        'auxiliar': 'Auxiliar Odontológico',
        'dentista': 'Dentista',
        'recepcionista': 'Recepcionista',
        'usuario': 'Usuario'
    }
    
    saludo = saludos.get(tipo_usuario, 'Usuario')
    
    asunto = f'Bienvenido a DentalForce - Credenciales de Acceso'
    mensaje = f"""
Estimado/a {saludo},

Se ha creado una cuenta para usted en DentalForce.

Credenciales de acceso:
- Usuario: {usuario.username}
- Contraseña temporal: {password_temporal}
- Correo: {usuario.email}

Por favor, inicie sesión y cambie su contraseña en el primer acceso.

URL de acceso: {settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8001'}

Saludos,
Equipo DentalForce
    """.strip()
    
    try:
        # Intentar enviar email
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
            logger.info(f"Credenciales enviadas por email a {usuario.email}")
            return True
        else:
            # Si no hay configuración de email, solo loggear
            logger.warning(f"EMAIL NO CONFIGURADO. Credenciales para {usuario.username}: {password_temporal}")
            print(f"\n{'='*60}")
            print(f"CREDENCIALES GENERADAS PARA: {usuario.username}")
            print(f"Email: {usuario.email}")
            print(f"Password temporal: {password_temporal}")
            print(f"{'='*60}\n")
            return False
            
    except Exception as e:
        logger.error(f"Error al enviar email a {usuario.email}: {str(e)}")
        print(f"\n⚠️  ERROR AL ENVIAR EMAIL")
        print(f"Usuario: {usuario.username}")
        print(f"Password temporal: {password_temporal}")
        print(f"Error: {str(e)}\n")
        return False


def enviar_credenciales_a_destinatario(email_destinatario, nombre_usuario, password_temporal, 
                                        tipo_usuario='usuario', clinica_nombre='', sucursal_nombre=''):
    """
    Envía las credenciales de un nuevo usuario a un email específico.
    
    Usado cuando se crean usuarios automáticamente (por ej. en sucursales) y las credenciales
    se envían al admin de la clínica en lugar del usuario temporal creado.
    
    Args:
        email_destinatario (str): Email donde enviar las credenciales
        nombre_usuario (str): Username del nuevo usuario creado
        password_temporal (str): Contraseña temporal generada
        tipo_usuario (str): Tipo de usuario (auxiliar, dentista, admin_clinica)
        clinica_nombre (str): Nombre de la clínica
        sucursal_nombre (str): Nombre de la sucursal (opcional)
    
    Returns:
        bool: True si se envió exitosamente, False en caso contrario
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Determinar descripción según tipo de usuario
    descripciones = {
        'admin_clinica': 'Administrador de Clínica',
        'auxiliar': 'Auxiliar Odontológico',
        'dentista': 'Dentista / Profesional Odontológico',
        'recepcionista': 'Recepcionista',
        'usuario': 'Usuario'
    }
    
    descripcion = descripciones.get(tipo_usuario, 'Usuario')
    
    # Construir mensajecon información de contexto
    ubicacion = f" en {sucursal_nombre}" if sucursal_nombre else ""
    
    asunto = f'Credenciales de Acceso - {descripcion} Creado en {clinica_nombre}'
    mensaje = f"""
Se ha creado una nueva cuenta de {descripcion} en DentalForce.

INFORMACIÓN DE LA CLÍNICA:
- Clínica: {clinica_nombre}{ubicacion}

DATOS DEL NUEVO USUARIO:
- Tipo: {descripcion}
- Usuario: {nombre_usuario}
- Contraseña Temporal: {password_temporal}

INSTRUCCIONES:
1. Comunique estos datos al {descripcion.lower()} de forma segura
2. El usuario debe ingresar con estas credenciales en el primer acceso
3. Al ingresar, le pedirá cambiar la contraseña temporal por una nueva
4. Acceder desde: {settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8001'}

IMPORTANTE:
- No comparta estas credenciales por canales no seguros
- Esta contraseña es temporal y debe cambiarla en el primer acceso
- Si el usuario olvida la contraseña, usará la opción "Olvidé mi contraseña"

Saludos,
Equipo DentalForce
    """.strip()
    
    try:
        # Intentar enviar email
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_destinatario],
                fail_silently=False
            )
            logger.info(f"✅ Credenciales enviadas a {email_destinatario} para {nombre_usuario} ({tipo_usuario})")
            return True
        else:
            # SMTP no configurado
            logger.warning(f"⚠️  Email no configurado. Registro de credenciales:")
            logger.warning(f"   Destinatario: {email_destinatario}")
            logger.warning(f"   Usuario: {nombre_usuario}")
            logger.warning(f"   Tipo: {tipo_usuario}")
            logger.warning(f"   Clínica: {clinica_nombre}")
            print(f"\n⚠️  EMAIL NO CONFIGURADO")
            print(f"Destinatario: {email_destinatario}")
            print(f"Usuario: {nombre_usuario}")
            print(f"Password temporal: {password_temporal}\n")
            return False
            
    except Exception as e:
        logger.error(f"Error al enviar credenciales a {email_destinatario}: {str(e)}")
        print(f"\n⚠️  ERROR AL ENVIAR EMAIL A {email_destinatario}")
        print(f"Usuario: {nombre_usuario}")
        print(f"Tipo: {tipo_usuario}")
        print(f"Password temporal: {password_temporal}")
        print(f"Error: {str(e)}\n")
        return False
