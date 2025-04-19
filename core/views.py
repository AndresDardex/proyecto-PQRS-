from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ClienteRegistroForm, LoginForm
from .models import Cliente, Empleado, PQRS


def home(request):
    return render(request, 'inicio.html')


def registrar_cliente(request):
    registro_exitoso = False
    if request.method == 'POST':
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            registro_exitoso = True
    else:
        form = ClienteRegistroForm()
    return render(request, 'registrar.html', {'form': form, 'registro_exitoso': registro_exitoso})


def login_personalizado(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            numero_id = form.cleaned_data['numero_identificacion']
            contrasena = form.cleaned_data['contrasena']

            try:
                cliente = Cliente.objects.get(numero_identificacion=numero_id)

                if cliente.contrasena == contrasena:
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
    return render(request, 'cliente_dashboard.html', {'usuario': usuario})


def vista_gestor(request):
    usuario = request.session.get('usuario', 'Invitado')
    return render(request, 'gestor_dashboard.html', {'usuario': usuario})


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

        PQRS.objects.create(
            tipo_radicado=tipo,
            comentarios=comentarios,
            anexo=anexo,
            cliente=cliente
        )

        messages.success(request, '¡Tu PQRS ha sido enviada con éxito!')
        return redirect('crear_pqrs')

    return render(request, 'crear-pqrs.html', {'usuario': cliente.nombre_completo})


def error_page(request):
    return render(request, 'error_pagina.html')
