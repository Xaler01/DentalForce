"""
Template tags personalizados para verificar permisos granulares de DentalForce
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def tiene_permiso(context, codigo_permiso):
    """
    Verifica si el usuario actual tiene un permiso granular específico.
    
    Uso en templates:
        {% load permisos_tags %}
        {% tiene_permiso 'recepcion.crear_cita' as puede_crear_cita %}
        {% if puede_crear_cita %}
            <a href="...">Crear Cita</a>
        {% endif %}
    
    Args:
        context: Contexto del template (contiene request)
        codigo_permiso: Código del permiso (ej: 'recepcion.crear_cita')
    
    Returns:
        bool: True si el usuario tiene el permiso, False en caso contrario
    """
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return False
    
    # Super admin tiene todos los permisos
    if request.user.is_superuser:
        return True
    
    # Verificar permiso granular
    try:
        user_clinica = request.user.clinica_asignacion
        return user_clinica.tiene_permiso(codigo_permiso)
    except:
        return False


@register.filter
def tiene_permisos(user, codigo_permiso):
    """
    Filtro para verificar permisos granulares.
    
    Uso en templates:
        {% load permisos_tags %}
        {% if user|tiene_permisos:'recepcion.crear_cita' %}
            <a href="...">Crear Cita</a>
        {% endif %}
    
    Args:
        user: Usuario actual
        codigo_permiso: Código del permiso
    
    Returns:
        bool: True si tiene el permiso
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        user_clinica = user.clinica_asignacion
        return user_clinica.tiene_permiso(codigo_permiso)
    except:
        return False


@register.simple_tag(takes_context=True)
def tiene_cualquier_permiso(context, *codigos_permisos):
    """
    Verifica si el usuario tiene AL MENOS UNO de los permisos listados.
    
    Uso:
        {% tiene_cualquier_permiso 'recepcion.ver_citas' 'recepcion.crear_cita' as puede_ver_citas %}
        {% if puede_ver_citas %}
            <a href="{% url 'cit:cita_list' %}">Agenda</a>
        {% endif %}
    """
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return False
    
    if request.user.is_superuser:
        return True
    
    try:
        user_clinica = request.user.clinica_asignacion
        for codigo in codigos_permisos:
            if user_clinica.tiene_permiso(codigo):
                return True
        return False
    except:
        return False


@register.simple_tag(takes_context=True)
def tiene_todos_permisos(context, *codigos_permisos):
    """
    Verifica si el usuario tiene TODOS los permisos listados.
    
    Uso:
        {% tiene_todos_permisos 'facturacion.crear_factura' 'facturacion.ver_facturas' as puede_facturar %}
    """
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return False
    
    if request.user.is_superuser:
        return True
    
    try:
        user_clinica = request.user.clinica_asignacion
        for codigo in codigos_permisos:
            if not user_clinica.tiene_permiso(codigo):
                return False
        return True
    except:
        return False
