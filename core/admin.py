from django.contrib import admin
from .models import Cliente, Empleado, PQRS

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'tipo_identificacion', 'numero_identificacion', 'correo_electronico', 'telefono_movil')
    search_fields = ('nombre_completo', 'numero_identificacion', 'correo_electronico')
    list_filter = ('tipo_identificacion',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'cedula', 'telefono', 'cliente')
    search_fields = ('nombre', 'apellido', 'cedula')
    list_filter = ('cliente',)

@admin.register(PQRS)
class PQRSAdmin(admin.ModelAdmin):
    list_display = ('numero_radicado', 'fecha_radicado', 'tipo_radicado', 'cliente')
    search_fields = ('numero_radicado', 'tipo_radicado', 'cliente__nombre_completo')
    list_filter = ('tipo_radicado', 'fecha_radicado')