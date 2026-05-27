"""Flujo de procesamiento de reservaciones usando Template Method."""

from abc import ABC
from django.core.exceptions import ValidationError

from reservaciones.models import Reservacion
from reservaciones.forms import fechas_en_temporada
from reservaciones.notificador import notificador


class ReservacionTemplate(ABC):
    """Template Method base para procesar una reservación.

    Define el esqueleto del algoritmo y permite que subclases
    extiendan pasos individuales.
    """

    def __init__(self, request, hospedaje, form):
        """Recibe el contexto necesario para crear una reservacion.

        Args:
            request: Peticion HTTP con el usuario autenticado.
            hospedaje: Hospedaje seleccionado para la reservacion.
            form: Formulario ya construido con los datos de la reserva.
        """

        self.request = request
        self.hospedaje = hospedaje
        self.form = form

    def procesar_reservacion(self):
        """Ejecuta el flujo completo para validar, crear y notificar la reserva."""

        if not self.form.is_valid():
            return None
        self.cleaned = self.form.cleaned_data
        try:
            self.validar_reglas_adicionales()
        except ValidationError as e:
            # Añadir error al formulario para ser mostrado en la vista
            self.form.add_error(None, e)
            return None

        precio_total = self.calcular_precio_total()
        reservacion = self.crear_reservacion(precio_total)
        self.post_procesamiento(reservacion)
        return reservacion

    def validar_reglas_adicionales(self):
        """Hook opcional para validaciones específicas."""
        return None

    def calcular_precio_total(self):
        """Calcula el precio base usando noches, unidades y precio unitario."""

        num_noches = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        unidades = self.cleaned["unidades_reservadas"]
        precio = self.hospedaje.precio_por_unidad
        return precio * unidades * num_noches

    def crear_reservacion(self, precio_total):
        """Persiste la reservacion activa asociada al usuario autenticado."""

        r = Reservacion.objects.create(
            fecha_inicio=self.cleaned["fecha_inicio"],
            fecha_fin=self.cleaned["fecha_fin"],
            num_huespedes=self.cleaned["num_huespedes"],
            unidades_reservadas=self.cleaned["unidades_reservadas"],
            precio_total=precio_total,
            hospedaje=self.hospedaje,
            usuario=self.request.user,
        )
        return r

    def post_procesamiento(self, reservacion):
        """Hook para acciones posteriores (notificaciones, logs, etc.)."""
        notificador.notificar("creada", reservacion)
        return None


class ReservacionHospedajeTemplate(ReservacionTemplate):
    """Implementación concreta para hospedajes.

    Aplica validaciones adicionales y recargos por temporada.
    """

    def validar_reglas_adicionales(self):
        """Impide estancias mayores al maximo permitido por el negocio."""

        max_noches = 30
        duracion = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        if duracion > max_noches:
            raise ValidationError(f"La estancia no puede exceder {max_noches} noches.")

    def calcular_precio_total(self):
        """Aplica recargo de temporada sobre el precio base."""

        base = super().calcular_precio_total()
        if fechas_en_temporada(self.cleaned["fecha_inicio"], self.cleaned["fecha_fin"]):
            return base * 1.20
        return base

    def post_procesamiento(self, reservacion):
        """Ejecuta acciones posteriores definidas por la plantilla base."""

        super().post_procesamiento(reservacion)
        return None
