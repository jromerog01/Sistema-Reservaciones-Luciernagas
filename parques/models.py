from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Model

class Servicio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Parque(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=300)

    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-90.000000")),
            MaxValueValidator(Decimal("90.000000")),
        ],
    )

    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-180.000000")),
            MaxValueValidator(Decimal("180.000000")),
        ],
    )

    horario_apertura = models.TimeField()
    horario_cierre = models.TimeField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    servicios = models.ManyToManyField(
        Servicio,
        related_name="parques",
        blank=True
    )


class Hospedaje(models.Model):
    class TipoHospedaje(models.TextChoices):
        CABANA = "CABANA", "Cabaña"
        CAMPING = "CAMPING", "Camping"

    parque = models.ForeignKey(
        Parque,
        on_delete=models.CASCADE,
        related_name="hospedajes"
    )

    tipo_hospedaje = models.CharField(
        max_length=20,
        choices=TipoHospedaje.choices
    )

    cantidad_unidades = models.PositiveIntegerField()
    capacidad_unidad = models.PositiveIntegerField()

    precio_por_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.parque.nombre} - {self.get_tipo_hospedaje_display()}"


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parque", "tipo_hospedaje"],
                name="hospedaje_unico_por_parque_y_tipo"
            )
        ]