from django import forms
from .models import Cliente, PQRS
from django.contrib.auth.hashers import make_password
import re

class ClienteRegistroForm(forms.ModelForm):
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña"
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}),
        label="Confirmar Contraseña"
    )

    class Meta:
        model = Cliente
        fields = [
            'tipo_identificacion',
            'numero_identificacion',
            'nombre_completo',
            'correo_electronico',
            'telefono_movil',
            'contrasena',
        ]

    def clean_contrasena(self):
        contrasena = self.cleaned_data.get('contrasena')

        # Validar que la contraseña tenga mínimo 8 caracteres, una mayúscula, una minúscula, un número y un caracter especial
        if len(contrasena) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', contrasena):
            raise forms.ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        if not re.search(r'[a-z]', contrasena):
            raise forms.ValidationError('La contraseña debe contener al menos una letra minúscula.')
        if not re.search(r'\d', contrasena):
            raise forms.ValidationError('La contraseña debe contener al menos un número.')
        if not re.search(r'[^\w\s]', contrasena):
            raise forms.ValidationError('La contraseña debe contener al menos un carácter especial.')

        return contrasena

    def clean(self):
        cleaned_data = super().clean()
        contrasena = cleaned_data.get("contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if contrasena and confirmar_contrasena and contrasena != confirmar_contrasena:
            raise forms.ValidationError("Las contraseñas no coinciden.")

    def save(self, commit=True):
        cliente = super().save(commit=False)
        cliente.contrasena = make_password(self.cleaned_data['contrasena'])  # Encriptar contraseña
        if commit:
            cliente.save()
        return cliente

class LoginForm(forms.Form):
    numero_identificacion = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su número de identificación'
        })
    )
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )

class FiltroPQRSForm(forms.Form):
    numero_radicado = forms.CharField(
        required=False,
        label='Número de Radicado',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por número de radicado'})
    )
    tipo_radicado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + PQRS.TIPO_RADICADO_CHOICES,
        label='Tipo de Radicado',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_inicio = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )