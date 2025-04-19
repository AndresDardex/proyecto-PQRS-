"""PQRS_Sistem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path
from core.views import (
    registrar_cliente, login_personalizado, vista_cliente,
    vista_gestor, cerrar_sesion, listar_pqrs_cliente, detalle_pqrs,
    gestionar_pqrs, detalle_pqrs_gestor
)
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='inicio.html'), name='inicio'),
    path('registrar/', registrar_cliente, name='registrar_cliente'),
    path('iniciar-sesion/', login_personalizado, name='login'),
    path('cliente/', vista_cliente, name='vista_cliente'),
    path('gestor/', vista_gestor, name='vista_gestor'),
    path('gestor/pqrs/', gestionar_pqrs, name='gestion_pqrs'),
    path('gestor/pqrs/<int:numero_radicado>/', detalle_pqrs_gestor, name='detalle_pqrs_gestor'),
    path('logout/', cerrar_sesion, name='cerrar_sesion'),
    path('cliente/pqrs/', listar_pqrs_cliente, name='listar_pqrs'),
    path('cliente/pqrs/<int:numero_radicado>/', detalle_pqrs, name='detalle_pqrs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)