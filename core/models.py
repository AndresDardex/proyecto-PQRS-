from django.db import models

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

    numero_radicado = models.AutoField(primary_key=True)
    fecha_radicado = models.DateTimeField(auto_now_add=True)
    tipo_radicado = models.CharField(max_length=25, choices=TIPO_RADICADO_CHOICES)
    comentarios = models.TextField()
    anexo = models.FileField(upload_to='anexos/', blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pqrs')

    def __str__(self):
        return f"Radicado #{self.numero_radicado} - {self.tipo_radicado}"