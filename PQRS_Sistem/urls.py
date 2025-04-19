from django.contrib import admin
from django.urls import path
<<<<<<< HEAD
from core.views import (registrar_cliente, login_personalizado, vista_cliente, vista_gestor, cerrar_sesion, crear_pqrs,
                        error_page)
=======
from core.views import (
    registrar_cliente, login_personalizado, vista_cliente,
    vista_gestor, cerrar_sesion, listar_pqrs_cliente, detalle_pqrs,
    gestionar_pqrs, detalle_pqrs_gestor
)
>>>>>>> origin/main
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
<<<<<<< HEAD
    path('crear-pqrs/', crear_pqrs, name='crear_pqrs'),
    path('error_pagina/', error_page, name='error_pagina'),
=======
    path('cliente/pqrs/', listar_pqrs_cliente, name='listar_pqrs'),
    path('cliente/pqrs/<int:numero_radicado>/', detalle_pqrs, name='detalle_pqrs'),
>>>>>>> origin/main
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)