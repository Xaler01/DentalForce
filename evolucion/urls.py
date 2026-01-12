from django.urls import path
from . import views

app_name = 'evolucion'

urlpatterns = [
    # Evoluciones
    path('', views.lista_evoluciones, name='lista'),
    path('nueva/<int:paciente_id>/', views.nueva_evolucion, name='nueva'),
    path('<int:pk>/', views.detalle_evolucion, name='detalle'),
    path('<int:pk>/editar/', views.editar_evolucion, name='editar'),
    path('<int:pk>/procedimientos/', views.editar_procedimientos_evolucion, name='editar_procedimientos'),
    path('<int:evolucion_pk>/procedimientos/<int:procedimiento_pk>/eliminar/', 
         views.eliminar_procedimiento_evolucion, name='eliminar_procedimiento'),
    
    # Planes de tratamiento
    path('planes/', views.lista_planes, name='lista_planes'),
    path('planes/nuevo/<int:paciente_id>/', views.nuevo_plan, name='nuevo_plan'),
    path('planes/<int:pk>/', views.detalle_plan, name='detalle_plan'),
    path('planes/<int:pk>/editar/', views.editar_plan, name='editar_plan'),
    path('planes/<int:pk>/procedimientos/', views.editar_procedimientos_plan, name='editar_procedimientos_plan'),
    
    # Historia clínica
    path('historia/<int:paciente_id>/', views.historia_clinica, name='historia_clinica'),
    path('historia/<int:paciente_id>/detalle/', views.detalle_historia_clinica, name='detalle_historia'),
]
