from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UsuarioManager(UserManager):
    """Permite autenticar usuarios por username o por correo electronico."""

    def get_by_natural_key(self, identificador):
        try:
            return self.get(username__iexact=identificador)
        except self.model.DoesNotExist:
            return self.get(email__iexact=identificador)


class Usuario(AbstractUser):
    """Usuario del sistema con rol explicito para controlar permisos."""

    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    email = models.EmailField(unique=True)

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE
    )

    objects = UsuarioManager()

    def es_cliente(self):
        """Indica si el usuario debe operar con permisos de cliente."""
        return self.rol == self.Rol.CLIENTE

    def es_administrador(self):
        """Centraliza la regla de acceso administrativo del proyecto."""
        return self.rol == self.Rol.ADMINISTRADOR or self.is_staff

    def update(self, **kwargs):
        """Actualiza campos simples del usuario y reporta si la operacion fue exitosa."""
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)

            self.save()
            return True

        except Exception:
            return False
   
    def __str__(self):
        return self.get_full_name() or self.email or self.username
