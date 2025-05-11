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
    numero_radicado = forms.IntegerField(required=False, label='Número de Radicado')
    tipo_radicado = forms.ChoiceField(
        choices=[('', 'Todos')] + list(PQRS.TIPO_RADICADO_CHOICES),
        required=False,
        label='Tipo de Radicado'
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos')] + list(PQRS.ESTADO_RADICADO_CHOICES),
        required=False,
        label='Estado'
    )
    fecha_inicio = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    fecha_fin = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class FiltroPQRSFormCliente(forms.Form):
    numero_radicado = forms.IntegerField(
        label="Número de Radicado",
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Buscar por número'})
    )

    tipo_radicado = forms.ChoiceField(
        label="Tipo de PQRS",
        choices=PQRS.TIPO_RADICADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    estado = forms.ChoiceField(
        label="Estado",
        choices=PQRS.ESTADO_RADICADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    fecha_inicio = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    fecha_fin = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError("La fecha de inicio no puede ser mayor a la fecha fin")

        return cleaned_data

class CambioContrasenaForm(forms.Form):
    contrasena_actual = forms.CharField(widget=forms.PasswordInput, label="Contraseña Actual")
    nueva_contrasena = forms.CharField(widget=forms.PasswordInput, label="Nueva Contraseña")
    confirmar_contrasena = forms.CharField(widget=forms.PasswordInput, label="Confirmar Nueva Contraseña")