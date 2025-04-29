# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    TIPO_IDENTIFICACION_CHOICES = [
        ('Cédula de Ciudadanía', 'Cédula de Ciudadanía'),
        ('Tarjeta de Identidad', 'Tarjeta de Identidad'),
        ('Cédula de Extranjería', 'Cédula de Extranjería'),
        ('Pasaporte', 'Pasaporte'),
    ]

    tipo_identificacion = models.CharField(max_length=50, choices=TIPO_IDENTIFICACION_CHOICES)
    numero_identificacion = models.CharField(max_length=20, unique=True)
    nombre_completo = models.CharField(max_length=100)
    correo_electronico = models.EmailField(unique=True)
    telefono_movil = models.CharField(max_length=15)
    contrasena = models.CharField(max_length=100)
    verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=64, blank=True, null=True)


    def __str__(self):
        return self.nombre_completo

class Empleado(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, to_field='numero_identificacion', db_column='numero_identificacion')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.cedula}"

class PQRS(models.Model):
    TIPO_RADICADO_CHOICES = [
        ('Petición', 'Petición'),
        ('Queja', 'Queja'),
        ('Reclamo', 'Reclamo'),
        ('Sugerencia', 'Sugerencia'),
    ]
    
    ESTADO_RADICADO_CHOICES = [
        ('Nuevo', 'Nuevo'),
        ('En Proceso', 'En Proceso'),
        ('Resuelto', 'Resuelto'),
        ('Cerrado', 'Cerrado'),
    ]

    numero_radicado = models.AutoField(primary_key=True)
    fecha_radicado = models.DateTimeField(auto_now_add=True)
    tipo_radicado = models.CharField(max_length=25, choices=TIPO_RADICADO_CHOICES)
    comentarios = models.TextField()
    anexo = models.FileField(upload_to='anexos/', blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pqrs')
    estado = models.CharField(max_length=20, choices=ESTADO_RADICADO_CHOICES, default='En Proceso')
    empleado_asignado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='pqrs_asignados')
    justificacion_del_estado = models.TextField(blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Radicado #{self.numero_radicado} - {self.tipo_radicado}"