from django.urls import path
from usuarios.views import (
    UsuarioListView,
    UsuarioCreateView,
    UsuarioUpdateView,
    UsuarioDeleteView,
)

app_name = 'usuarios'

urlpatterns = [
    # Listar usuarios
    path('', UsuarioListView.as_view(), name='lista'),
    
    # Crear usuario
    path('crear/', UsuarioCreateView.as_view(), name='crear'),
    
    # Editar usuario
    path('<int:pk>/editar/', UsuarioUpdateView.as_view(), name='editar'),
    
    # Eliminar usuario (soft delete)
    path('<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='eliminar'),
]
