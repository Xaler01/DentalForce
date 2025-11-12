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
]
