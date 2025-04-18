from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ClienteRegistroForm
from .models import Cliente, Empleado
from .forms import LoginForm
from django.shortcuts import get_object_or_404
from .models import PQRS

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
                    # Verificar si también es empleado
                    if Empleado.objects.filter(cliente=numero_id).exists():
                        # Redirigir a vista de gestor
                        request.session['usuario'] = cliente.nombre_completo
                        request.session['rol'] = 'gestor'
                        return redirect('vista_gestor')
                    else:
                        # Redirigir a vista de cliente
                        request.session['usuario'] = cliente.nombre_completo
                        request.session['rol'] = 'cliente'
                        return redirect('vista_cliente')
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

# views.py

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
