from django import forms
from .models import Cliente, PQRS

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

    def clean(self):
        cleaned_data = super().clean()
        contrasena = cleaned_data.get("contrasena")
        confirmar_contrasena = cleaned_data.get("confirmar_contrasena")

        if contrasena and confirmar_contrasena and contrasena != confirmar_contrasena:
            raise forms.ValidationError("Las contraseñas no coinciden.")

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