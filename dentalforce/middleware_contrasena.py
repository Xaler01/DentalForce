"""
Middleware para forzar cambio de contraseña temporal en primer login.

Si el usuario tiene contraseña temporal, redirige a cambiar-contraseña
excepto en rutas permitidas.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser


class ForzarCambioContrasenaTemporalMiddleware:
    """
    Middleware que detecta usuarios con contraseña temporal y
    redirige a la vista de cambio de contraseña.
    """
    
    # Rutas permitidas (no requieren cambio de contraseña)
    RUTAS_PERMITIDAS = [
        '/usuarios/cambiar-contrasena/',  # La página de cambio en sí
        '/logout/',  # Permitir logout
        '/admin/',  # Panel admin
        '/static/',  # Archivos estáticos
        '/media/',  # Archivos multimedia
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo procesar si el usuario está autenticado
        if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
            # Verificar si está en ruta permitida
            if not any(request.path.startswith(ruta) for ruta in self.RUTAS_PERMITIDAS):
                try:
                    # Obtener relación usuario-clínica
                    user_clinica = request.user.clinica_asignacion
                    
                    # Si tiene contraseña temporal, redirigir
                    if user_clinica.contrasena_temporal:
                        return redirect('usuarios:cambiar_contrasena')
                except:
                    # Si no hay relación usuario-clínica, permitir pasar
                    pass
        
        response = self.get_response(request)
        return response
