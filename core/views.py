from django.shortcuts import render, redirect
from django.contrib import messages  # Importa el framework de mensajes
from .forms import ClienteRegistroForm

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
