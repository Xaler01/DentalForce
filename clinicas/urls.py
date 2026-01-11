from django.urls import path
from . import views

app_name = 'clinicas'

urlpatterns = [
    # Selector de clínica
    path('seleccionar/', views.ClinicaSelectView.as_view(), name='seleccionar'),
    
    # CRUD Clínicas
    path('', views.ClinicaListView.as_view(), name='list'),
    path('<int:pk>/', views.ClinicaDetailView.as_view(), name='detail'),
    path('create/', views.ClinicaCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ClinicaUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ClinicaDeleteView.as_view(), name='delete'),
    
    # CRUD Sucursales
    path('sucursales/', views.SucursalListView.as_view(), name='sucursal_list'),
    path('sucursales/<int:pk>/', views.SucursalDetailView.as_view(), name='sucursal_detail'),
    path('sucursales/create/', views.SucursalCreateView.as_view(), name='sucursal_create'),
    path('sucursales/<int:pk>/edit/', views.SucursalUpdateView.as_view(), name='sucursal_update'),
    path('sucursales/<int:pk>/delete/', views.SucursalDeleteView.as_view(), name='sucursal_delete'),
    
    # CRUD Especialidades
    path('especialidades/', views.EspecialidadListView.as_view(), name='especialidad_list'),
    path('especialidades/<int:pk>/', views.EspecialidadDetailView.as_view(), name='especialidad_detail'),
    path('especialidades/create/', views.EspecialidadCreateView.as_view(), name='especialidad_create'),
    path('especialidades/<int:pk>/edit/', views.EspecialidadUpdateView.as_view(), name='especialidad_update'),
    path('especialidades/<int:pk>/delete/', views.EspecialidadDeleteView.as_view(), name='especialidad_delete'),
    
    # CRUD Cubículos
    path('cubiculos/', views.CubiculoListView.as_view(), name='cubiculo_list'),
    path('cubiculos/<int:pk>/', views.CubiculoDetailView.as_view(), name='cubiculo_detail'),
    path('cubiculos/create/', views.CubiculoCreateView.as_view(), name='cubiculo_create'),
    path('cubiculos/<int:pk>/edit/', views.CubiculoUpdateView.as_view(), name='cubiculo_update'),
    path('cubiculos/<int:pk>/delete/', views.CubiculoDeleteView.as_view(), name='cubiculo_delete'),
]
