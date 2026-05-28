from abc import ABC
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import transaction

from reservaciones.models import Reservacion
from reservaciones.forms import fechas_en_temporada, unidades_disponibles
from reservaciones.utils.notificador import notificador


class ReservacionTemplate(ABC):
    """Template Method base para procesar una reservacion.

    Define el esqueleto del algoritmo y permite que subclases extiendan pasos
    específicos sin duplicar validaciones, persistencia ni notificaciones.
    """

    def __init__(self, request, hospedaje, form):
        self.request = request
        self.hospedaje = hospedaje
        self.form = form

    def procesar_reservacion(self):
        """Ejecuta el flujo completo de validacion y creacion de reserva."""
        if not self.form.is_valid():
            return None
        self.cleaned = self.form.cleaned_data

        try:
            with transaction.atomic():
                # Bloquea el hospedaje para que dos solicitudes simultaneas no
                # confirmen cupos sobre la misma disponibilidad.
                self.hospedaje = self.hospedaje.__class__.objects.select_for_update().get(pk=self.hospedaje.pk)
                self.validar_reglas_adicionales()

                disponibles = unidades_disponibles(
                    self.hospedaje,
                    self.cleaned["fecha_inicio"],
                    self.cleaned["fecha_fin"],
                )
                if self.cleaned["unidades_reservadas"] > disponibles:
                    self.form.add_error(
                        "unidades_reservadas",
                        f"Solo quedan {disponibles} unidad(es) disponible(s) para ese periodo en este hospedaje."
                    )
                    return None

                precio_total = self.calcular_precio_total()
                reservacion = self.crear_reservacion(precio_total)
                self.post_procesamiento(reservacion)
                return reservacion
        except ValidationError as e:
            # Añadir error al formulario para ser mostrado en la vista
            self.form.add_error(None, e)
            return None

    def validar_reglas_adicionales(self):
        """Hook opcional para validaciones especificas."""
        return None

    def calcular_precio_total(self):
        """Calcula el precio base del hospedaje para la estancia."""
        num_noches = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        unidades = self.cleaned["unidades_reservadas"]
        precio = self.hospedaje.precio_por_unidad
        return precio * unidades * num_noches

    def crear_reservacion(self, precio_total):
        """Persiste la reservacion ya validada dentro de la transaccion."""
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
    """Implementacion concreta para hospedajes.

    Aplica validaciones adicionales y recargos por temporada alta.
    """

    def validar_reglas_adicionales(self):
        """Limita estancias demasiado largas para proteger la disponibilidad."""
        max_noches = 30
        duracion = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        if duracion > max_noches:
            raise ValidationError(f"La estancia no puede exceder {max_noches} noches.")

    def calcular_precio_total(self):
        """Agrega recargo de temporada a las reservas validas del festival."""
        base = super().calcular_precio_total()
        if fechas_en_temporada(self.cleaned["fecha_inicio"], self.cleaned["fecha_fin"]):
            return (base * Decimal("1.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return base

    def post_procesamiento(self, reservacion):
        """Dispara notificaciones y deja un punto de extension para el flujo."""
        super().post_procesamiento(reservacion)
        return None
