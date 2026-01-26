"""
Utilidades para gestión de usuarios en PowerDent
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


def generar_email_temporal(username, dominio='powerdent.local'):
    """
    Genera un email temporal basado en el username.
    
    Args:
        username (str): Nombre de usuario
        dominio (str): Dominio del email (default: powerdent.local)
    
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
    
    asunto = f'Bienvenido a PowerDent - Credenciales de Acceso'
    mensaje = f"""
Estimado/a {saludo},

Se ha creado una cuenta para usted en PowerDent.

Credenciales de acceso:
- Usuario: {usuario.username}
- Contraseña temporal: {password_temporal}
- Correo: {usuario.email}

Por favor, inicie sesión y cambie su contraseña en el primer acceso.

URL de acceso: {settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8001'}

Saludos,
Equipo PowerDent
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
