import random
import string

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