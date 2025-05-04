import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generar_contrasena_segura(longitud=8):
    if longitud < 4:
        raise ValueError("La longitud debe ser al menos 4 para cumplir los requisitos mínimos.")

    mayuscula = random.choice(string.ascii_uppercase)
    minuscula = random.choice(string.ascii_lowercase)
    numero = random.choice(string.digits)
    especial = random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?")

    obligatorios = [mayuscula, minuscula, numero, especial]

    if longitud > 4:
        restantes = random.choices(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?", k=longitud - 4)
        obligatorios += restantes

    random.shuffle(obligatorios)
    return ''.join(obligatorios)

def enviar_correo_bienvenida(email, nombre, numero_id, contrasena, numero_radicado, tipo_radicado, codigo_verificacion):
    asunto = 'Bienvenido al sistema de PQRS - Verifica tu cuenta'
    mensaje = f'''
Hola {nombre},

Tu cuenta ha sido creada exitosamente en nuestra plataforma de PQRS.

Aquí están tus datos de acceso:

👤 Usuario: {numero_id}
🔐 Contraseña temporal: {contrasena}

Detalles de tu PQRS:

📄 Número de radicado: {numero_radicado}
📂 Tipo de radicado: {tipo_radicado}

Para activar tu cuenta y confirmar que no eres un bot, por favor haz clic en el siguiente enlace de verificación:

🔗 http://localhost:8000/verificar/{codigo_verificacion}

Una vez verificado, podrás iniciar sesión en nuestra plataforma y gestionar tus solicitudes. Te recomendamos cambiar la contraseña tras el primer acceso.

Gracias por confiar en nosotros.

Si no te registraste, por favor ignora este mensaje.

Atentamente,
Equipo de PQRS
    '''
    remitente = settings.EMAIL_HOST_USER
    send_mail(asunto, mensaje, remitente, [email])