from django.db import models
from django.db.models import Model, ForeignKey
from django.core.validators import MinValueValidator

from parques.models import Hospedaje
from proyectoLuciernagas import settings
from usuarios.models import Usuario


class Reservacion(models.Model):
    class EstadoReservacion(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        CANCELADA = "CANCELADA", "Cancelada"
        FINALIZADA = "FINALIZADA", "Finalizada"

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    num_huespedes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    unidades_reservadas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoReservacion.choices,
        default=EstadoReservacion.ACTIVA
    )

    hospedaje = models.ForeignKey(
        "parques.Hospedaje",
        on_delete=models.PROTECT,
        related_name="reservaciones"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservaciones"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservación #{self.id} - {self.usuario}"

    def calcular_duracion(self):
        return (self.fecha_fin - self.fecha_inicio).days

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_inicio__lt=models.F("fecha_fin")),
                name="fecha_inicio_menor_fecha_fin"
            )
        ]
