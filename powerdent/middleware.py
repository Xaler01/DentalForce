"""
Middleware para aislamiento multi-tenant por clínica
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class ClinicaMiddleware:
    """
    Middleware que asegura que exista una clínica activa en la sesión
    para todas las vistas excepto login, logout, y selector de clínica.
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
            clinica_id = request.session.get('clinica_id')
            
            # Si no hay clínica en sesión, redirigir al selector
            if not clinica_id:
                # No mostrar mensaje si ya está en la página de selección
                if not (path.startswith('/clinicas/seleccionar/') or path.startswith('/clinica/seleccionar/')):
                    messages.warning(
                        request,
                        'Debe seleccionar una clínica para continuar.'
                    )
                    return redirect('clinicas:seleccionar')
        
        response = self.get_response(request)
        return response
