"""
Rutas para el módulo de Pacientes (SOOD-46)
"""
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Lista de pacientes con búsqueda
    path('', views.PacienteListView.as_view(), name='paciente-list'),
    
    # Crear nuevo paciente
    path('crear/', views.PacienteCreateView.as_view(), name='paciente-create'),
    
    # Detalle de paciente
    path('<int:pk>/', views.PacienteDetailView.as_view(), name='paciente-detail'),
    
    # Editar paciente
    path('<int:pk>/editar/', views.PacienteUpdateView.as_view(), name='paciente-update'),
    
    # Eliminar (desactivar) paciente
    path('<int:pk>/eliminar/', views.PacienteDeleteView.as_view(), name='paciente-delete'),

    # Reactivar paciente desactivado
    path('<int:pk>/reactivar/', views.PacienteReactivateView.as_view(), name='paciente-reactivate'),

    # Gestión rápida de enfermedades (AJAX)
    path('<int:pk>/enfermedades/agregar/', views.PacienteEnfermedadAddView.as_view(), name='paciente-enfermedad-add'),
    path('<int:pk>/enfermedades/<int:ep_id>/eliminar/', views.PacienteEnfermedadDeleteView.as_view(), name='paciente-enfermedad-delete'),
    
    # API AJAX para alertas (SOOD-87)
    path('<int:pk>/alertas/detalles/', views.PacienteAlertasDetallesAJAXView.as_view(), name='paciente-alertas-detalles'),
]
