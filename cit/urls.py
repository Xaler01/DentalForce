from django.urls import path
from . import views

app_name = 'cit'

urlpatterns = [
    # ========================================================================
    # CRUD de Citas
    # ========================================================================
    path('citas/', views.CitaListView.as_view(), name='cita-list'),
    path('citas/nueva/', views.CitaCreateView.as_view(), name='cita-create'),
    path('citas/<int:pk>/', views.CitaDetailView.as_view(), name='cita-detail'),
    path('citas/<int:pk>/editar/', views.CitaUpdateView.as_view(), name='cita-update'),
    path('citas/<int:pk>/cancelar/', views.CitaCancelView.as_view(), name='cita-cancel'),
    
    # ========================================================================
    # Cambios de Estado
    # ========================================================================
    path('citas/<int:pk>/confirmar/', views.confirmar_cita, name='cita-confirmar'),
    path('citas/<int:pk>/iniciar/', views.iniciar_atencion_cita, name='cita-iniciar'),
    path('citas/<int:pk>/completar/', views.completar_cita, name='cita-completar'),
    path('citas/<int:pk>/no-asistio/', views.marcar_no_asistio, name='cita-no-asistio'),
    path('citas/<int:pk>/cambiar-estado/', views.cambiar_estado_cita_ajax, name='cambiar-estado-cita'),
    
    # ========================================================================
    # API / AJAX Endpoints
    # ========================================================================
    path('api/disponibilidad/dentista/', 
         views.check_dentista_disponibilidad, 
         name='ajax-dentista-disponibilidad'),
    
    path('api/disponibilidad/cubiculo/', 
         views.check_cubiculo_disponibilidad, 
         name='ajax-cubiculo-disponibilidad'),
    
    path('api/dentista/<int:dentista_id>/especialidades/', 
         views.get_dentista_especialidades, 
         name='ajax-dentista-especialidades'),
    
    path('api/especialidad/<int:especialidad_id>/dentistas/', 
         views.get_especialidad_dentistas, 
         name='ajax-especialidad-dentistas'),
    
    path('api/citas/<int:pk>/mover/', 
         views.mover_cita, 
         name='ajax-mover-cita'),
    # Backwards-compatible alias expected by tests
    path('api/citas/<int:pk>/mover/', 
         views.mover_cita, 
         name='mover-cita'),
    
    path('api/pacientes/buscar/', 
         views.buscar_pacientes, 
         name='ajax-buscar-pacientes'),
    
    # ========================================================================
    # Calendario
    # ========================================================================
     path('calendario/', views.CalendarioCitasView.as_view(), name='calendario'),
     # Alias para compatibilidad con tests
     path('calendario/', views.CalendarioCitasView.as_view(), name='calendario-citas'),
    path('api/citas.json', views.citas_json, name='citas-json'),
    
    # ========================================================================
    # CRUD de Especialidades
    # ========================================================================
    path('especialidades/', views.EspecialidadListView.as_view(), name='especialidad-list'),
    path('especialidades/nueva/', views.EspecialidadCreateView.as_view(), name='especialidad-create'),
    path('especialidades/<int:pk>/editar/', views.EspecialidadUpdateView.as_view(), name='especialidad-update'),
    path('especialidades/<int:pk>/eliminar/', views.EspecialidadDeleteView.as_view(), name='especialidad-delete'),
    
    # ========================================================================
    # CRUD de Dentistas
    # ========================================================================
    path('dentistas/', views.DentistaListView.as_view(), name='dentista-list'),
    path('dentistas/nuevo/', views.DentistaCreateView.as_view(), name='dentista-create'),
    path('dentistas/<int:pk>/editar/', views.DentistaUpdateView.as_view(), name='dentista-update'),
    path('dentistas/<int:pk>/eliminar/', views.DentistaDeleteView.as_view(), name='dentista-delete'),
    
    # ========================================================================
    # CRUD de Clínicas
    # ========================================================================
    path('clinicas/', views.ClinicaListView.as_view(), name='clinica-list'),
    path('clinicas/nueva/', views.ClinicaCreateView.as_view(), name='clinica-create'),
    path('clinicas/<int:pk>/', views.ClinicaDetailView.as_view(), name='clinica-detail'),
    path('clinicas/<int:pk>/editar/', views.ClinicaUpdateView.as_view(), name='clinica-update'),
    path('clinicas/<int:pk>/eliminar/', views.ClinicaDeleteView.as_view(), name='clinica-delete'),
    path('clinicas/<int:pk>/activar/', views.ClinicaActivateView.as_view(), name='clinica-activate'),
    
    # ========================================================================
    # CRUD de Sucursales
    # ========================================================================
    path('sucursales/', views.SucursalListView.as_view(), name='sucursal-list'),
    path('sucursales/nueva/', views.SucursalCreateView.as_view(), name='sucursal-create'),
    path('sucursales/<int:pk>/', views.SucursalDetailView.as_view(), name='sucursal-detail'),
    path('sucursales/<int:pk>/editar/', views.SucursalUpdateView.as_view(), name='sucursal-update'),
    path('sucursales/<int:pk>/eliminar/', views.SucursalDeleteView.as_view(), name='sucursal-delete'),
    path('sucursales/<int:pk>/activar/', views.SucursalActivateView.as_view(), name='sucursal-activate'),
]
