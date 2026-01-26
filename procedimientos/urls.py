"""
URLs para gestión de procedimientos odontológicos y precios por clínica.
"""
from django.urls import path
from . import views

app_name = 'procedimientos'

urlpatterns = [
    # Procedimientos
    path('', views.ProcedimientoListView.as_view(), name='procedimiento-list'),
    path('crear/', views.ProcedimientoCreateView.as_view(), name='procedimiento-create'),
    path('<int:pk>/editar/', views.ProcedimientoUpdateView.as_view(), name='procedimiento-update'),
    path('<int:pk>/eliminar/', views.ProcedimientoDeleteView.as_view(), name='procedimiento-delete'),
    
    # Precios por clínica
    path('precios/', views.ClinicaProcedimientoListView.as_view(), name='precio-list'),
    path('precios/crear/', views.ClinicaProcedimientoCreateView.as_view(), name='precio-create'),
    path('precios/<int:pk>/editar/', views.ClinicaProcedimientoUpdateView.as_view(), name='precio-update'),
    path('precios/<int:pk>/eliminar/', views.ClinicaProcedimientoDeleteView.as_view(), name='precio-delete'),
]
