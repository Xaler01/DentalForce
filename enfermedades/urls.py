"""
URLs del módulo de enfermedades.
Namespace: 'enfermedades'
"""
from django.urls import path
from . import views

app_name = 'enfermedades'

urlpatterns = [
    # URLs de CategoriaEnfermedad (SOOD-82 - Fase 3)
    # path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    # path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    # path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    # path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
    
    # URLs de Enfermedad (SOOD-83 - Fase 3)
    # path('', views.EnfermedadListView.as_view(), name='enfermedad_list'),
    # path('crear/', views.EnfermedadCreateView.as_view(), name='enfermedad_create'),
    # path('<int:pk>/', views.EnfermedadDetailView.as_view(), name='enfermedad_detail'),
    # path('<int:pk>/editar/', views.EnfermedadUpdateView.as_view(), name='enfermedad_update'),
    # path('<int:pk>/eliminar/', views.EnfermedadDeleteView.as_view(), name='enfermedad_delete'),
    
    # API AJAX para alertas (SOOD-87 - Fase 3)
    # path('paciente/<int:paciente_id>/alertas/', views.obtener_alertas_ajax, name='alertas_ajax'),
]
