from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario


class RegistroForm(UserCreationForm):
    """Formulario de alta de clientes usando las validaciones de Django."""

    email = forms.EmailField()

    class Meta:
        model = Usuario
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]


class LoginForm(AuthenticationForm):
    """Formulario de acceso; acepta username o correo como identificador."""

    username = forms.CharField(
        label='Usuario o Correo'
    )
