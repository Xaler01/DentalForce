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
from django.conf import settings
from django.conf.urls.static import static
from powerdent.views import inicio, inicio2

# from powerdent import inicio, inicio2

urlpatterns = [

    path('', include(('bases.urls', 'bases'), namespace='bases')),
    path('inv/', include(('inv.urls', 'inv'), namespace='inv')),
    path('cmp/', include(('cmp.urls', 'cmp'), namespace='cmp')),
    path('cit/', include(('cit.urls', 'cit'), namespace='cit')),
    path('clinicas/', include(('clinicas.urls', 'clinicas'), namespace='clinicas')),
    path('pacientes/', include(('pacientes.urls', 'pacientes'), namespace='pacientes')),
    path('enfermedades/', include(('enfermedades.urls', 'enfermedades'), namespace='enfermedades')),  # SOOD-70
    path('usuarios/', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),  # SOOD-USU: Gestión de usuarios

    path('admin/', admin.site.urls),
    # path('', inicio, name='Inicio'),  # La ruta raíz ahora renderiza el index.html
    # path('Inicio/', inicio),
    # path('Iniciored/', inicio2),
]

# Servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)