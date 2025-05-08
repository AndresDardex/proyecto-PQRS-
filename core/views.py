from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ClienteRegistroForm, LoginForm, FiltroPQRSFormCliente
from .models import Cliente, Empleado, PQRS
from .forms import ClienteRegistroForm
from django.utils.dateparse import parse_datetime
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
from .utils import generar_contrasena_segura, enviar_correo_bienvenida
from datetime import datetime
from django.utils import timezone
import uuid
import csv
import pytz

def home(request):
    return render(request, 'inicio.html')

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
        filters = {}

        if form.cleaned_data['numero_radicado']:
            filters['numero_radicado'] = form.cleaned_data['numero_radicado']

        if form.cleaned_data['tipo_radicado']:
            filters['tipo_radicado'] = form.cleaned_data['tipo_radicado']

        if form.cleaned_data['estado']:
            filters['estado'] = form.cleaned_data['estado']

        if form.cleaned_data['fecha_inicio']:
            fecha_inicio = datetime.combine(form.cleaned_data['fecha_inicio'], datetime.min.time())
            filters['fecha_radicado__gte'] = fecha_inicio

        if form.cleaned_data['fecha_fin']:
            fecha_fin = datetime.combine(form.cleaned_data['fecha_fin'], datetime.max.time())
            filters['fecha_radicado__lte'] = fecha_fin

        pqrs_queryset = pqrs_queryset.filter(**filters)

    if 'exportar_csv' in request.GET:
        return exportar_pqrs_csv(pqrs_queryset)

    return render(request, 'gestion_pqrs.html', {
        'usuario': request.session.get('usuario'),
        'pqrs_list': pqrs_queryset,
        'form': form
    })


def actualizar_pqrs(request, numero_radicado):
    if request.method == 'POST' and request.session.get('rol') == 'gestor':
        try:
            pqrs = get_object_or_404(PQRS, numero_radicado=numero_radicado)

            nuevo_estado = request.POST.get('estado')
            nota_estado = request.POST.get('nota_estado', '').strip()
            fecha_respuesta_str = request.POST.get('fecha_respuesta')

            # Validaciones
            if not nota_estado:
                messages.error(request, 'Debe ingresar una nota para el cambio de estado')
                return redirect('detalle_pqrs_gestor', numero_radicado=numero_radicado)

            if not fecha_respuesta_str:
                messages.error(request, 'Debe seleccionar una fecha de respuesta')
                return redirect('detalle_pqrs_gestor', numero_radicado=numero_radicado)

            # Convertir y validar fecha
            fecha_respuesta_dt = parse_datetime(fecha_respuesta_str)
            if not fecha_respuesta_dt:
                messages.error(request, 'Formato de fecha inválido')
                return redirect('detalle_pqrs_gestor', numero_radicado=numero_radicado)

            # Validar que la fecha sea diferente a la última
            if pqrs.fecha_respuesta and fecha_respuesta_dt == pqrs.fecha_respuesta:
                messages.error(request, 'Debe modificar la fecha de respuesta para cambiar el estado')
                return redirect('detalle_pqrs_gestor', numero_radicado=numero_radicado)

            # Crear registro histórico
            registro_historico = (
                f"{fecha_respuesta_dt.strftime('%d/%m/%Y %H:%M:%S')} - "
                f"Estado cambiado a {nuevo_estado}\n"
                f"Nota: {nota_estado}\n"
                "----------------------------------------\n"
            )

            # Actualizar campos
            pqrs.estado = nuevo_estado
            pqrs.fecha_respuesta = fecha_respuesta_dt
            pqrs.justificacion_del_estado = (
                    registro_historico +
                    (pqrs.justificacion_del_estado if pqrs.justificacion_del_estado else '')
            )

            pqrs.save()

            messages.success(request, 'Los cambios se han guardado correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')

    return redirect('detalle_pqrs_gestor', numero_radicado=numero_radicado)


def exportar_pqrs_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_pqrs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Número Radicado', 'Fecha', 'Tipo', 'Estado', 'Cliente', 'Comentarios'])

    for pqrs in queryset:
        writer.writerow([
            pqrs.numero_radicado,
            pqrs.fecha_radicado.strftime("%Y-%m-%d %H:%M"),
            pqrs.tipo_radicado,
            pqrs.estado,
            pqrs.cliente.nombre_completo,
            pqrs.comentarios
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
    pqrs_queryset = PQRS.objects.filter(cliente=cliente).order_by('-fecha_radicado')

    form = FiltroPQRSFormCliente(request.GET or None)

    if form.is_valid():
        filters = {'cliente': cliente}

        print("Datos del formulario:", form.cleaned_data)  # Debug

        if form.cleaned_data['numero_radicado']:
            filters['numero_radicado'] = form.cleaned_data['numero_radicado']

        if form.cleaned_data['tipo_radicado']:
            filters['tipo_radicado'] = form.cleaned_data['tipo_radicado']

        if form.cleaned_data['estado']:
            print(f"Filtrando por estado: {form.cleaned_data['estado']}")  # Debug
            filters['estado'] = form.cleaned_data['estado']

        if form.cleaned_data['fecha_inicio']:
            fecha_inicio = datetime.combine(form.cleaned_data['fecha_inicio'], datetime.min.time())
            filters['fecha_radicado__gte'] = fecha_inicio

        if form.cleaned_data['fecha_fin']:
            fecha_fin = datetime.combine(form.cleaned_data['fecha_fin'], datetime.max.time())
            filters['fecha_radicado__lte'] = fecha_fin

        print("Filtros aplicados:", filters)  # Debug
        pqrs_queryset = pqrs_queryset.filter(**filters)
        print("Resultados:", pqrs_queryset)  # Debug

    return render(request, 'listar_pqrs.html', {
        'pqrs_list': pqrs_queryset,
        'usuario': nombre_usuario,
        'form': form
    })

def detalle_pqrs(request, numero_radicado):
    if request.session.get('rol') != 'cliente':
        return redirect('inicio')

    nombre_usuario = request.session.get('usuario')
    cliente = get_object_or_404(Cliente, nombre_completo=nombre_usuario)
    pqrs = get_object_or_404(PQRS, numero_radicado=numero_radicado, cliente=cliente)

    return render(request, 'detalle_pqrs.html', {'pqrs': pqrs, 'usuario': nombre_usuario})


def detalle_pqrs_gestor(request, numero_radicado):
    pqrs = get_object_or_404(PQRS, numero_radicado=numero_radicado)
    estados = PQRS.ESTADO_RADICADO_CHOICES

    return render(request, 'detalle_pqrs_gestor.html', {
        'pqrs': pqrs,
        'estados': estados,
        'now': timezone.localtime(timezone.now())
    })

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
                    # Generar y encriptar contraseña
                    contrasena_plana = generar_contrasena_segura()
                    usuario_nuevo = True
                    contrasena_encriptada = make_password(contrasena_plana)
                    # Generar código de verificación
                    codigo_verificacion = str(uuid.uuid4())
                    # Si no existe, crear nuevo cliente
                    cliente_data = {
                        'tipo_identificacion': request.POST.get('tipo_documento'),
                        'numero_identificacion': numero_documento,
                        'nombre_completo': request.POST.get('nombre'),
                        'correo_electronico': email,
                        'telefono_movil': request.POST.get('telefono'),
                        'contrasena': contrasena_encriptada,
                        'codigo_verificacion': codigo_verificacion,  # Guardamos el código
                        'verificado': False
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

                    # Enviar correo con datos de acceso
                enviar_correo_bienvenida(cliente.correo_electronico,
                        cliente.nombre_completo,
                        cliente.numero_identificacion,
                        contrasena_plana,
                        pqrs.numero_radicado,
                        pqrs.tipo_radicado,
                        cliente.codigo_verificacion  # Lo usas en el enlace
                    )

                return JsonResponse({
                    'success': True,
                    'numero_radicado': pqrs.numero_radicado,
                    'usuario_nuevo': usuario_nuevo,
                    'email': cliente.correo_electronico,
                    'password': contrasena_plana if usuario_nuevo else None,
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


