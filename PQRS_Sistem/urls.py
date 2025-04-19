from django.contrib import admin
from django.urls import path
from core.views import (registrar_cliente, login_personalizado, vista_cliente, vista_gestor, cerrar_sesion, crear_pqrs,
                        error_page)
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='inicio.html'), name='inicio'),
    path('registrar/', registrar_cliente, name='registrar_cliente'),
    path('iniciar-sesion/', login_personalizado, name='login'),
    path('cliente/', vista_cliente, name='vista_cliente'),
    path('gestor/', vista_gestor, name='vista_gestor'),
    path('logout/', cerrar_sesion, name='cerrar_sesion'),
    path('crear-pqrs/', crear_pqrs, name='crear_pqrs'),
    path('error_pagina/', error_page, name='error_pagina'),
]
