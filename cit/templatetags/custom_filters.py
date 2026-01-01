from django import template
from django.contrib.auth.models import User

register = template.Library()


@register.filter
def get_user_name(user_id):
    """
    Obtiene el nombre completo o username de un usuario por su ID.
    Si el usuario no existe, retorna un guión.
    """
    if not user_id:
        return '-'
    
    try:
        user = User.objects.get(id=user_id)
        full_name = user.get_full_name()
        return full_name if full_name else user.username
    except User.DoesNotExist:
        return '-'
