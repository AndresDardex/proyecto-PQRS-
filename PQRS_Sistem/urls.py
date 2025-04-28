from django.contrib import admin
from django.urls import path

from core.views import (
    registrar_cliente, login_personalizado, vista_cliente,
    vista_gestor, cerrar_sesion, listar_pqrs_cliente, detalle_pqrs,
    gestionar_pqrs, detalle_pqrs_gestor, error_page, crear_pqrs, registrar_cliente_pqrs
)

from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='inicio.html'), name='inicio'),
    path('registrar/', registrar_cliente, name='registrar_cliente'),
    path('iniciar-sesion/', login_personalizado, name='iniciar_sesion'),
    path('cliente/', vista_cliente, name='vista_cliente'),
    path('gestor/', vista_gestor, name='vista_gestor'),
    path('gestor/pqrs/', gestionar_pqrs, name='gestion_pqrs'),
    path('gestor/pqrs/<int:numero_radicado>/', detalle_pqrs_gestor, name='detalle_pqrs_gestor'),
    path('logout/', cerrar_sesion, name='cerrar_sesion'),
    path('crear-pqrs/', crear_pqrs, name='crear_pqrs'),
    path('error_pagina/', error_page, name='error_pagina'),
    path('cliente/pqrs/', listar_pqrs_cliente, name='listar_pqrs'),
    path('cliente/pqrs/<int:numero_radicado>/', detalle_pqrs, name='detalle_pqrs'),
    path('registrar-pqrs/', registrar_cliente_pqrs, name='registrar_cliente_pqrs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)