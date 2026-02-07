"""
Middleware para aislamiento multi-tenant por clínica
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.models import User


class ClinicaMiddleware:
    """
    Middleware que asegura que exista una clínica activa en la sesión
    para todas las vistas excepto login, logout, y selector de clínica.
    
    Enforza restricciones multi-tenant:
    - Super admin (is_superuser=True): acceso a todo, no restricción de clínica
    - Usuario normal: require UsuarioClinica existente, setea clinica_id en sesión
    - Usuario sin asignación: 403 Forbidden (excepto en vistas especiales)
    """
    
    # Vistas que no requieren clínica activa
    EXEMPT_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/cit/clinicas/seleccionar/',  # Selector de clínica (ruta completa)
        '/clinicas/seleccionar/',      # Nuevo selector en módulo clinicas
        '/clinica/seleccionar/',       # Variante antigua por compatibilidad
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar si la ruta está exenta
        path = request.path_info
        is_exempt = any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)
        
        # Si el usuario está autenticado y la ruta no está exenta
        if request.user.is_authenticated and not is_exempt:
            # ======== SUPER ADMIN: SIN RESTRICCIONES ========
            if request.user.is_superuser:
                # Super admin no está restringido a clínica
                # Pero puede seleccionar una para el contexto
                request.clinica = None
                request.rol_usuario = None
                response = self.get_response(request)
                return response
            
            # ======== USUARIO NORMAL: REQUIRE UsuarioClinica ========
            try:
                from usuarios.models import UsuarioClinica
                
                user_clinica = UsuarioClinica.objects.select_related('clinica').get(
                    usuario=request.user,
                    activo=True
                )
                
                # Setear clinica_id en sesión (usado por views)
                request.session['clinica_id'] = user_clinica.clinica.id
                request.session['rol_usuario'] = user_clinica.rol
                
                # Setear en request para acceso directo en vistas
                request.clinica = user_clinica.clinica
                request.rol_usuario = user_clinica.rol
                
            except Exception:
                # Usuario sin UsuarioClinica o no activo: FORBID
                # (excepto en vistas especiales de selección)
                if not (path.startswith('/clinicas/seleccionar/') or path.startswith('/clinica/seleccionar/')):
                    return HttpResponseForbidden(
                        "No tienes acceso a ninguna clínica. Contacta al administrador."
                    )
        
        response = self.get_response(request)
        return response

