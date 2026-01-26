from django.urls import path
from usuarios.views import (
    UsuarioListView,
    UsuarioCreateView,
    UsuarioUpdateView,
    UsuarioDeleteView,
    PerfilUsuarioView,
    RolListView,
    RolDetailView,
    PermisoListView,
    UsuarioRolesUpdateView,
)

app_name = 'usuarios'

urlpatterns = [
    # Listar usuarios
    path('', UsuarioListView.as_view(), name='lista'),
    
    # Crear usuario
    path('crear/', UsuarioCreateView.as_view(), name='crear'),
    
    # Editar usuario (requiere permisos admin)
    path('<int:pk>/editar/', UsuarioUpdateView.as_view(), name='editar'),
    
    # Editar mi perfil (no requiere permisos admin)
    path('mi-perfil/', PerfilUsuarioView.as_view(), name='mi_perfil'),
    
    # Eliminar usuario (soft delete)
    path('<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='eliminar'),
    
    # ================================
    # GESTIÓN DE ROLES Y PERMISOS
    # ================================
    
    # Listar roles disponibles
    path('roles/', RolListView.as_view(), name='roles_list'),
    
    # Detalle de un rol
    path('roles/<int:pk>/', RolDetailView.as_view(), name='rol_detail'),
    
    # Listar permisos
    path('permisos/', PermisoListView.as_view(), name='permisos_list'),
    
    # Asignar roles y permisos a usuario
    path('<int:pk>/roles/', UsuarioRolesUpdateView.as_view(), name='usuario_roles'),
]
