"""
URL configuration for powerdent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from powerdent.views import inicio, inicio2

# from powerdent import inicio, inicio2

urlpatterns = [

    path('', include(('bases.urls', 'bases'), namespace='bases')),
    path('inv/', include(('inv.urls', 'inv'), namespace='inv')),
    path('cmp/', include(('cmp.urls', 'cmp'), namespace='cmp')),
    path('cit/', include(('cit.urls', 'cit'), namespace='cit')),

    path('admin/', admin.site.urls),
    # path('', inicio, name='Inicio'),  # La ruta raíz ahora renderiza el index.html
    # path('Inicio/', inicio),
    # path('Iniciored/', inicio2),
]
