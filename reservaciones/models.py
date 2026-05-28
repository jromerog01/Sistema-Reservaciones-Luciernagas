# reservaciones/models.py

from django.db import models
from django.core.validators import MinValueValidator

from parques.models import Hospedaje
from proyectoLuciernagas import settings


class Reservacion(models.Model):
    """Reserva de hospedaje realizada por un cliente."""

    class EstadoReservacion(models.TextChoices):
        ACTIVA    = "ACTIVA",    "Activa"
        CANCELADA = "CANCELADA", "Cancelada"
        FINALIZADA = "FINALIZADA","Finalizada"

    fecha_inicio        = models.DateField()
    fecha_fin           = models.DateField()
    num_huespedes       = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unidades_reservadas = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_total        = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=EstadoReservacion.choices,
        default=EstadoReservacion.ACTIVA,
    )
    hospedaje = models.ForeignKey(
        "parques.Hospedaje", on_delete=models.PROTECT, related_name="reservaciones"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservación #{self.id} - {self.usuario}"

    def calcular_duracion(self):
        """Número de noches de la estancia, usando fecha_fin como checkout."""
        return (self.fecha_fin - self.fecha_inicio).days

    # Estos wrappers mantienen compatibilidad con tests y llamadas existentes
    # aunque la logica principal viva en reservaciones.forms.

    @staticmethod
    def calcular_unidades_necesarias(num_huespedes, capacidad_unidad):
        from reservaciones.forms import calcular_unidades_necesarias
        return calcular_unidades_necesarias(num_huespedes, capacidad_unidad)

    @staticmethod
    def calcular_precio_total(unidades_reservadas, precio_por_unidad, num_noches):
        from reservaciones.forms import calcular_precio_total
        return calcular_precio_total(unidades_reservadas, precio_por_unidad, num_noches)

    @staticmethod
    def fechas_en_temporada(fecha_inicio, fecha_fin):
        from reservaciones.forms import fechas_en_temporada
        return fechas_en_temporada(fecha_inicio, fecha_fin)

    @staticmethod
    def rango_incluye_martes(fecha_inicio, fecha_fin):
        from reservaciones.forms import rango_incluye_martes
        return rango_incluye_martes(fecha_inicio, fecha_fin)

    @staticmethod
    def unidades_disponibles(hospedaje, fecha_inicio, fecha_fin, excluir_id=None):
        from reservaciones.forms import unidades_disponibles
        return unidades_disponibles(hospedaje, fecha_inicio, fecha_fin, excluir_id)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_inicio__lt=models.F("fecha_fin")),
                name="fecha_inicio_menor_fecha_fin",
            )
        ]
