from django.contrib.auth.decorators import login_required
from django.contrib.messages import success
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ClienteRegistroForm, LoginForm, FiltroPQRSFormCliente, FiltroPQRSForm, RecuperarContrasenaForm
from django.utils.dateparse import parse_datetime
from .models import Cliente, Empleado, PQRS
from .forms import LoginForm, CambioContrasenaForm, RecuperarContrasenaForm, RestablecerContrasenaForm
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError
from .utils import generar_contrasena_segura, enviar_correo_bienvenida, enviar_correo_recuperacion
from datetime import datetime
from django.utils import timezone

from io import BytesIO
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

import uuid
import csv
import pytz
import random
import re

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

        empleados = Empleado.objects.all()
        if empleados.exists():
            empleado_asignado = random.choice(empleados)
        else:
            empleado_asignado = None

        nueva_pqrs = PQRS.objects.create(
            tipo_radicado=tipo,
            comentarios=comentarios,
            anexo=anexo,
            cliente=cliente,
            empleado_asignado=empleado_asignado
        )

        return redirect(f'/crear-pqrs/?registro_exitoso=1&radicado={nueva_pqrs.numero_radicado}')

    registro_exitoso = request.GET.get('registro_exitoso') == '1'
    numero_radicado = request.GET.get('radicado')

    return render(request, 'crear-pqrs.html', {
        'usuario': cliente.nombre_completo,
        'registro_exitoso': registro_exitoso,
        'numero_radicado': numero_radicado
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

    if 'exportar_pdf' in request.GET:
        return exportar_pqrs_pdf(pqrs_queryset)

    # Configuración de la paginación
    paginator = Paginator(pqrs_queryset, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'gestion_pqrs.html', {
        'usuario': request.session.get('usuario'),
        'page_obj': page_obj,
        'form': form
    })


def exportar_pqrs_pdf(queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_pqrs.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_normal.fontSize = 8
    style_normal.leading = 10

    # Título del reporte
    title = Paragraph("<b>Reporte de PQRS - Supermarket</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))  # Espacio

    # Configuración de la tabla principal
    data = [
        [
            Paragraph('<b>N° Radicado</b>', style_normal),
            Paragraph('<b>Fecha Radicado</b>', style_normal),
            Paragraph('<b>Tipo</b>', style_normal),
            Paragraph('<b>Estado</b>', style_normal),
            Paragraph('<b>Cliente</b>', style_normal),
            Paragraph('<b>Comentarios</b>', style_normal),
            Paragraph('<b>Fecha Respuesta</b>', style_normal)
        ]
    ]

    for pqrs in queryset:
        fecha_respuesta = pqrs.fecha_respuesta.strftime("%Y-%m-%d %H:%M") if pqrs.fecha_respuesta else "No asignada"

        nombre_cliente = pqrs.cliente.nombre_completo
        if len(nombre_cliente) > 25:
            partes = nombre_cliente.split()
            if len(partes) >= 3:
                nombre_cliente = f"{partes[0][0]}. {partes[1][0]}. {' '.join(partes[2:])}"

        data.append([
            Paragraph(str(pqrs.numero_radicado), style_normal),
            Paragraph(pqrs.fecha_radicado.strftime("%Y-%m-%d %H:%M"), style_normal),
            Paragraph(pqrs.tipo_radicado, style_normal),
            Paragraph(pqrs.get_estado_display(), style_normal),
            Paragraph(nombre_cliente, style_normal),
            Paragraph(pqrs.comentarios[:80] + '...' if len(pqrs.comentarios) > 80 else pqrs.comentarios, style_normal),
            Paragraph(fecha_respuesta, style_normal)
        ])

    # Crear tabla con ajuste automático
    table = Table(data, colWidths=[0.6 * inch, 1.1 * inch, 0.7 * inch, 0.8 * inch,
                                   1.2 * inch, 2.2 * inch, 1.0 * inch])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E1F2')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#7F7F7F')),
        ('WORDWRAP', (0, 0), (-1, -1)),
        ('LEADING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Pie de página con fecha
    elements.append(Paragraph(
        f"<i>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
        styles['Italic']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


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

def validar_contrasena_segura(password):
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'[0-9]', password) or
        not re.search(r'[@$!%*?&#._-]', password)):
        return False
    return True

def cambiar_contrasena(request):
    numero_id = request.session.get('numero_id')
    if not numero_id:
        return redirect('cambiar_contrasena')

    cliente = get_object_or_404(Cliente, numero_identificacion=numero_id)

    success = None
    error = None

    if request.method == 'POST':
        form = CambioContrasenaForm(request.POST)
        if form.is_valid():
            actual = form.cleaned_data['contrasena_actual']
            nueva = form.cleaned_data['nueva_contrasena']
            confirmar = form.cleaned_data['confirmar_contrasena']

            if not check_password(actual, cliente.contrasena):
                error = "La contraseña actual es incorrecta."
            elif nueva != confirmar:
                error = "Las nuevas contraseñas no coinciden."
            elif not validar_contrasena_segura(nueva):
                error = "La nueva contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial."
            else:
                cliente.contrasena = make_password(nueva)
                cliente.save()
                success = "La contraseña se actualizó correctamente."
                form = CambioContrasenaForm()

    else:
        form = CambioContrasenaForm()

    return render(request, 'cambiar_contrasena.html', {
        'form': form,
        'usuario': cliente.nombre_completo,
        'success': success,
        'error': error
    })

def solicitar_recuperacion(request):
    success = None
    error = None

    if request.method == 'POST':
        form = RecuperarContrasenaForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            try:
                cliente = Cliente.objects.get(correo_electronico=correo)
                enviar_correo_recuperacion(cliente, request)
                success = 'Te hemos enviado un correo con instrucciones para recuperar tu contraseña.'
            except Cliente.DoesNotExist:
                error = 'El correo no está registrado.'
    else:
        form = RecuperarContrasenaForm()

    return render(request, 'recuperar_contrasena.html', {
        'form': form,
        'success': success,
        'error': error
    })

def restablecer_contrasena(request, token):
    success = None
    error = None

    try:
        cliente = Cliente.objects.get(token_recuperacion=token)
    except Cliente.DoesNotExist:
        cliente = None

    if cliente is not None:
        if request.method == 'POST':
            form = RestablecerContrasenaForm(request.POST)
            if form.is_valid():
                nueva_contrasena = form.cleaned_data['nueva_contrasena']
                cliente.contrasena = make_password(nueva_contrasena)
                cliente.token_recuperacion = None  # Eliminar token después de usarlo
                cliente.save()
                success = 'Tu contraseña ha sido restablecida exitosamente.'
                return render(request, 'restablecer_contrasena.html', {
                    'form': form,
                    'success': success,
                })
        else:
            form = RestablecerContrasenaForm()
        return render(request, 'restablecer_contrasena.html', {
            'form': form,
            'error': error,
            'success': success
        })
    else:
        form = RestablecerContrasenaForm()
        error = 'El enlace de restablecimiento no es válido o ha expirado.'
        return render(request, 'restablecer_contrasena.html', {
            'form': form,
            'error': error,
            'success': success
        })

