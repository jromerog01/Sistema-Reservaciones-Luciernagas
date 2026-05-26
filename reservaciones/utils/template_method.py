from abc import ABC
from django.core.exceptions import ValidationError

from reservaciones.models import Reservacion
from reservaciones.forms import fechas_en_temporada


class ReservacionTemplate(ABC):
    """Template Method base para procesar una reservación.

    Define el esqueleto del algoritmo y permite que subclases
    extiendan pasos individuales.
    """

    def __init__(self, request, hospedaje, form):
        self.request = request
        self.hospedaje = hospedaje
        self.form = form

    def procesar_reservacion(self):
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
        num_noches = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        unidades = self.cleaned["unidades_reservadas"]
        precio = self.hospedaje.precio_por_unidad
        return precio * unidades * num_noches

    def crear_reservacion(self, precio_total):
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
        return None


class ReservacionHospedajeTemplate(ReservacionTemplate):
    """Implementación concreta para hospedajes.

    Aplica validaciones adicionales y recargos por temporada.
    """

    def validar_reglas_adicionales(self):
        max_noches = 30
        duracion = (self.cleaned["fecha_fin"] - self.cleaned["fecha_inicio"]).days
        if duracion > max_noches:
            raise ValidationError(f"La estancia no puede exceder {max_noches} noches.")

    def calcular_precio_total(self):
        base = super().calcular_precio_total()
        if fechas_en_temporada(self.cleaned["fecha_inicio"], self.cleaned["fecha_fin"]):
            return base * 1.20
        return base

    def post_procesamiento(self, reservacion):
        # Placeholder: aquí se podrían enviar emails, actualizar inventario, etc.
        return None
