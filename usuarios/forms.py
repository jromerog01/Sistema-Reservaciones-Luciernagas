from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario


class RegistroForm(UserCreationForm):

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

    username = forms.CharField(
        label='Usuario o Correo'
    )


class CrearAdminForm(UserCreationForm):
    """Formulario para que un admin cree otra cuenta de administrador."""

    email = forms.EmailField(label='Correo electrónico')

    class Meta:
        model = Usuario
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.ADMINISTRADOR
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        if commit:
            usuario.save()
        return usuario


class EditarPerfilForm(forms.ModelForm):
    """Formulario para que un usuario edite su información de cuenta."""

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username' : 'Username',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
        }