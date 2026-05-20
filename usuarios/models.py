from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class UsuarioManager(UserManager):
    def get_by_natural_key(self, identificador):
        try:
            return self.get(username__iexact=identificador)
        except self.model.DoesNotExist:
            return self.get(email__iexact=identificador)


class Usuario(AbstractUser):
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
        return self.rol == self.Rol.CLIENTE

    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR or self.is_staff

    def __str__(self):
        return self.get_full_name() or self.email or self.username
