from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ClienteRegistroForm, LoginForm
from .models import Cliente, Empleado, PQRS
from .forms import ClienteRegistroForm
from .models import Cliente, Empleado
from .forms import LoginForm
from django.shortcuts import get_object_or_404
from .models import PQRS
from .forms import FiltroPQRSForm
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db import models, IntegrityError
from django.core.mail import send_mail
from django.conf import settings
import uuid
import csv



def home(request):
    return render(request, 'inicio.html')


def registrar_cliente(request):
    registro_exitoso = False
    if request.method == 'POST':
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)  # No guarda aún, solo crea el objeto

            # Generar el código de verificación
            cliente.codigo_verificacion = str(uuid.uuid4())
            cliente.verificado = False

            cliente.save()  # Ahora sí guardamos en la base de datos

            # Enviar el correo de verificación
            enviar_correo_verificacion(cliente.correo_electronico, cliente.codigo_verificacion)

            registro_exitoso = True
    else:
        form = ClienteRegistroForm()

    return render(request, 'registrar.html', {'form': form, 'registro_exitoso': registro_exitoso})

def enviar_correo_verificacion(correo_destino, codigo):
    asunto = 'Verifica tu cuenta'
    mensaje = f'Gracias por registrarte. Para activar tu cuenta, haz clic aquí:\n\nhttp://localhost:8000/verificar/{codigo}\n\nSi no te registraste, por favor ignora este mensaje.'
    remitente = settings.EMAIL_HOST_USER  # Esto depende de tu configuración SMTP
    send_mail(asunto, mensaje, remitente, [correo_destino])

def verificar_cuenta(request, codigo):
    cliente = get_object_or_404(Cliente, codigo_verificacion=codigo)
    cliente.verificado = True
    cliente.codigo_verificacion = None  # Limpia el código
    cliente.save()
    return redirect('iniciar_sesion')  # Lo puedes redirigir a la página de login

def login_personalizado(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            numero_id = form.cleaned_data['numero_identificacion']
            contrasena = form.cleaned_data['contrasena']

            try:
                cliente = Cliente.objects.get(numero_identificacion=numero_id)

                if check_password(contrasena, cliente.contrasena): #comparación de la contraseña encriptada
                    request.session['usuario'] = cliente.nombre_completo
                    request.session['rol'] = 'gestor' if Empleado.objects.filter(
                        cliente=numero_id).exists() else 'cliente'
                    request.session['numero_id'] = cliente.numero_identificacion

                    return redirect('vista_gestor' if request.session['rol'] == 'gestor' else 'vista_cliente')
                else:
                    messages.error(request, 'Contraseña incorrecta.')
            except Cliente.DoesNotExist:
                messages.error(request, 'El usuario no existe.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def vista_cliente(request):
    usuario = request.session.get('usuario', 'Invitado')
    return render(request, 'vista_cliente.html', {'usuario': usuario})


def vista_gestor(request):
    usuario = request.session.get('usuario', 'Gestor Invitado')
    return render(request, 'vista_gestor.html', {'usuario': usuario})



def cerrar_sesion(request):
    request.session.flush()
    return redirect('inicio')


def crear_pqrs(request):
    numero_id = request.session.get('numero_id')
    if not numero_id:
        return redirect('error_pagina')

    try:
        cliente = Cliente.objects.get(numero_identificacion=numero_id)
    except Cliente.DoesNotExist:
        return redirect('error_pagina')

    if request.method == 'POST':
        tipo = request.POST.get('tipo_radicado')
        comentarios = request.POST.get('comentarios')
        anexo = request.FILES.get('anexo')

        # Crear PQRS
        PQRS.objects.create(
            tipo_radicado=tipo,
            comentarios=comentarios,
            anexo=anexo,
            cliente=cliente
        )

        # Redirigir con bandera para mostrar modal
        return redirect('/crear-pqrs/?registro_exitoso=1')

    registro_exitoso = request.GET.get('registro_exitoso') == '1'
    return render(request, 'crear-pqrs.html', {
        'usuario': cliente.nombre_completo,
        'registro_exitoso': registro_exitoso
    })


def error_page(request):
    return render(request, 'error_pagina.html')

def gestionar_pqrs(request):
    if request.session.get('rol') != 'gestor':
        return redirect('inicio')

    pqrs_queryset = PQRS.objects.all().select_related('cliente').order_by('-fecha_radicado')
    form = FiltroPQRSForm(request.GET or None)

    if form.is_valid():
        numero_radicado = form.cleaned_data.get('numero_radicado')
        tipo_radicado = form.cleaned_data.get('tipo_radicado')
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        if numero_radicado:
            pqrs_queryset = pqrs_queryset.filter(numero_radicado=numero_radicado)
        if tipo_radicado:
            pqrs_queryset = pqrs_queryset.filter(tipo_radicado=tipo_radicado)
        if fecha_inicio:
            pqrs_queryset = pqrs_queryset.filter(fecha_radicado__gte=fecha_inicio)
        if fecha_fin:
            pqrs_queryset = pqrs_queryset.filter(fecha_radicado__lte=fecha_fin)

    # Exportar a CSV
    if 'exportar_csv' in request.GET:
        return exportar_pqrs_csv(pqrs_queryset)

    return render(request, 'gestion_pqrs.html', {
        'usuario': request.session.get('usuario'),
        'pqrs_list': pqrs_queryset,
        'form': form
    })

def exportar_pqrs_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_pqrs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Número Radicado', 'Fecha', 'Tipo', 'Comentarios', 'Cliente'])

    for pqrs in queryset:
        writer.writerow([
            pqrs.numero_radicado,
            pqrs.fecha_radicado.strftime("%Y-%m-%d %H:%M"),
            pqrs.tipo_radicado,
            pqrs.comentarios,
            pqrs.cliente.nombre_completo
        ])

    return response

def cerrar_sesion(request):
    request.session.flush()  # Elimina todos los datos de sesión
    return redirect('inicio')  # Redirige al home


def listar_pqrs_cliente(request):
    if request.session.get('rol') != 'cliente':
        return redirect('inicio')

    nombre_usuario = request.session.get('usuario')
    cliente = get_object_or_404(Cliente, nombre_completo=nombre_usuario)
    pqrs = PQRS.objects.filter(cliente=cliente).order_by('-fecha_radicado')

    return render(request, 'listar_pqrs.html', {'pqrs_list': pqrs, 'usuario': nombre_usuario})

def detalle_pqrs(request, numero_radicado):
    if request.session.get('rol') != 'cliente':
        return redirect('inicio')

    nombre_usuario = request.session.get('usuario')
    cliente = get_object_or_404(Cliente, nombre_completo=nombre_usuario)
    pqrs = get_object_or_404(PQRS, numero_radicado=numero_radicado, cliente=cliente)

    return render(request, 'detalle_pqrs.html', {'pqrs': pqrs, 'usuario': nombre_usuario})

def detalle_pqrs_gestor(request, numero_radicado):
    pqrs = get_object_or_404(PQRS, numero_radicado=numero_radicado)
    return render(request, 'detalle_pqrs_gestor.html', {'pqrs': pqrs})


from django.db import transaction, models
from django.contrib.auth.hashers import make_password
from django.db.utils import IntegrityError
from django.http import JsonResponse
from .models import Cliente, PQRS


def registrar_cliente_pqrs(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                numero_documento = request.POST.get('numero_documento')
                email = request.POST.get('email')

                # Verificar si el cliente ya existe por número de identificación
                try:
                    cliente = Cliente.objects.get(numero_identificacion=numero_documento)
                    usuario_nuevo = False
                except Cliente.DoesNotExist:
                    # Si no existe, crear nuevo cliente
                    cliente_data = {
                        'tipo_identificacion': request.POST.get('tipo_documento'),
                        'numero_identificacion': numero_documento,
                        'nombre_completo': request.POST.get('nombre'),
                        'correo_electronico': email,
                        'telefono_movil': request.POST.get('telefono'),
                        'contrasena': make_password("Rz7U4;6_"),  # Contraseña quemada encriptada
                    }

                    cliente = Cliente.objects.create(**cliente_data)
                    usuario_nuevo = True

                # Crear PQRS asociada al cliente (tanto para nuevo como existente)
                pqrs_data = {
                    'tipo_radicado': request.POST.get('tipo_radicado'),
                    'comentarios': request.POST.get('comentarios'),
                    'cliente': cliente,
                }

                if 'anexo' in request.FILES:
                    pqrs_data['anexo'] = request.FILES['anexo']

                pqrs = PQRS.objects.create(**pqrs_data)

                # Configurar sesión solo si es nuevo usuario
                if usuario_nuevo:
                    request.session['usuario'] = cliente.nombre_completo
                    request.session['rol'] = 'cliente'
                    request.session['numero_id'] = cliente.numero_identificacion

                return JsonResponse({
                    'success': True,
                    'numero_radicado': pqrs.numero_radicado,
                    'usuario_nuevo': usuario_nuevo,
                    'email': cliente.correo_electronico,
                    'password': 'Rz7U4;6_' if usuario_nuevo else None,
                    'message': 'PQRS registrada exitosamente' +
                               (' y nuevo usuario creado' if usuario_nuevo else '')
                })

        except IntegrityError as e:
            return JsonResponse({
                'success': False,
                'message': 'Error: El número de documento o correo electrónico ya están registrados.'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al procesar la solicitud: {str(e)}'
            }, status=500)

    # GET request - mostrar formulario
    return render(request, 'registrar_cliente.html')