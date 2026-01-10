from django.urls import path
from . import views

app_name = 'clinicas'

urlpatterns = [
    path('seleccionar/', views.ClinicaSelectView.as_view(), name='seleccionar'),
]
