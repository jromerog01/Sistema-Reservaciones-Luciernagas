from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario


class RegistroForm(UserCreationForm):
    """Formulario para registrar clientes con el modelo de usuario personalizado."""

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
    """Formulario de autenticacion que acepta username o correo electronico."""

    username = forms.CharField(
        label='Usuario o Correo'
    )
