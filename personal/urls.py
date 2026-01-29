from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    path('', views.PersonalListView.as_view(), name='personal-list'),
    path('nuevo/', views.PersonalCreateView.as_view(), name='personal-create'),
    path('<int:pk>/editar/', views.PersonalUpdateView.as_view(), name='personal-update'),

    path('horas-extra/', views.PersonalHorasExtraListView.as_view(), name='horas-extra-list'),
    path('horas-extra/nuevo/', views.PersonalHorasExtraCreateView.as_view(), name='horas-extra-create'),
    path('horas-extra/<int:pk>/aprobar/', views.PersonalHorasExtraAprobarView.as_view(), name='horas-extra-approve'),
]
