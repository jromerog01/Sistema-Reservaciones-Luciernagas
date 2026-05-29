from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Model

class Servicio(models.Model):
    """Servicio que puede ofrecer uno o varios parques."""

    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Parque(models.Model):
    """Parque oficial participante en el festival."""

    class Estado(models.TextChoices):
        TLAXCALA = "TLAXCALA", "Tlaxcala"
        EDOMEX = "EDOMEX", "Estado de México"
        PUEBLA = "PUEBLA", "Puebla"

    nombre = models.CharField(max_length=100, unique=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.TLAXCALA,
    )
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["latitud", "longitud"],
                name="unique_coordinates"
            )
        ]

    servicios = models.ManyToManyField(
        Servicio,
        related_name="parques",
        blank=True
    )

    def __str__(self):
        return self.nombre

    def obtener_servicios(self):
        """Devuelve los servicios asociados como lista para adapters y vistas."""
        return list(self.servicios.all())

    def obtener_hospedajes(self):
        """Devuelve los hospedajes asociados como lista para adapters y vistas."""
        return list(self.hospedajes.all())

    @property
    def precio_minimo(self):
        """Precio mas bajo disponible entre los hospedajes del parque."""
        hospedajes = self.hospedajes.all()
        if hospedajes:
            return min(h.precio_por_unidad for h in hospedajes)
        return None


class Hospedaje(models.Model):
    """Tipo de alojamiento disponible dentro de un parque.

    Un registro representa un grupo de unidades del mismo tipo, no una unidad
    fisica individual. Esto simplifica el calculo de disponibilidad por fechas.
    """

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

    cantidad_unidades = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    capacidad_unidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    precio_por_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.parque.nombre} - {self.get_tipo_hospedaje_display()}"


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parque", "tipo_hospedaje"],
                name="hospedaje_unico_por_parque_y_tipo"
            )
        ]
