from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    # Gestión de Personal
    path('', views.PersonalListView.as_view(), name='personal-list'),
    path('nuevo/', views.PersonalCreateView.as_view(), name='personal-create'),
    path('<int:pk>/editar/', views.PersonalUpdateView.as_view(), name='personal-update'),

    # Horas Extra
    path('horas-extra/', views.PersonalHorasExtraListView.as_view(), name='horas-extra-list'),
    path('horas-extra/nuevo/', views.PersonalHorasExtraCreateView.as_view(), name='horas-extra-create'),
    path('horas-extra/<int:pk>/editar/', views.PersonalHorasExtraUpdateView.as_view(), name='horas-extra-update'),
    path('horas-extra/<int:pk>/eliminar/', views.PersonalHorasExtraDeleteView.as_view(), name='horas-extra-delete'),
    path('horas-extra/<int:pk>/aprobar/', views.PersonalHorasExtraAprobarView.as_view(), name='horas-extra-approve'),
    path('horas-extra/<int:pk>/detalle/', views.PersonalHorasExtraDetalleView.as_view(), name='horas-extra-detalle'),
    
    # Aprobación Masiva y Reportes
    path('horas-extra/aprobar-masiva/', views.PersonalHorasExtraAprobarMasivaView.as_view(), name='horas-extra-aprobar-masiva'),
    path('nomina/reporte/', views.PersonalNominaReporteView.as_view(), name='nomina-reporte'),
]
