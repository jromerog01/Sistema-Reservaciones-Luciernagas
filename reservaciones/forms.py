"""Formularios y reglas de negocio para crear reservaciones."""

from datetime import date, timedelta
import math

from django import forms
from django.db import models as dj_models

from reservaciones.models import Reservacion

MESES_TEMPORADA = {6, 7, 8}


def calcular_unidades_necesarias(num_huespedes, capacidad_unidad):
    """Calcula las unidades de hospedaje requeridas para alojar huespedes."""

    if capacidad_unidad <= 0:
        raise ValueError("La capacidad por unidad debe ser mayor que cero.")
    return math.ceil(num_huespedes / capacidad_unidad)


def calcular_precio_total(unidades_reservadas, precio_por_unidad, num_noches):
    """Calcula el costo base segun unidades, precio unitario y noches."""

    return precio_por_unidad * unidades_reservadas * num_noches


def unidades_ocupadas_en_periodo(hospedaje_id, fecha_inicio, fecha_fin, excluir_id=None):
    """Suma unidades activas que se solapan con el rango solicitado."""

    qs = Reservacion.objects.filter(
        hospedaje_id=hospedaje_id,
        estado=Reservacion.EstadoReservacion.ACTIVA,
        fecha_inicio__lt=fecha_fin,
        fecha_fin__gt=fecha_inicio,
    )
    if excluir_id is not None:
        qs = qs.exclude(id=excluir_id)
    resultado = qs.aggregate(total=dj_models.Sum("unidades_reservadas"))
    return resultado["total"] or 0


def unidades_disponibles(hospedaje, fecha_inicio, fecha_fin, excluir_id=None):
    """Calcula disponibilidad real para un hospedaje y rango de fechas."""

    ocupadas = unidades_ocupadas_en_periodo(hospedaje.id, fecha_inicio, fecha_fin, excluir_id)
    return hospedaje.cantidad_unidades - ocupadas


def fechas_en_temporada(fecha_inicio, fecha_fin):
    """Valida que todas las noches de estancia caigan entre junio y agosto."""

    ultima_noche = fecha_fin - timedelta(days=1)
    return (
        fecha_inicio.month in MESES_TEMPORADA
        and ultima_noche.month in MESES_TEMPORADA
    )


def rango_incluye_martes(fecha_inicio, fecha_fin):
    """Detecta si alguna noche de la estancia cae en martes."""

    dia = fecha_inicio
    while dia < fecha_fin:
        if dia.weekday() == 1:  # 1 = martes
            return True
        dia += timedelta(days=1)
    return False


class ReservacionForm(forms.Form):
    """Valida fechas, capacidad y disponibilidad antes de crear una reservacion."""

    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de llegada",
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de salida",
    )
    num_huespedes = forms.IntegerField(
        min_value=1,
        label="Número de huéspedes",
    )
    unidades_reservadas = forms.IntegerField(
        min_value=1,
        label="Unidades a reservar",
    )


    def __init__(self, *args, hospedaje=None, reservacion_id=None, **kwargs):
        """Inicializa el formulario con el hospedaje usado para validar cupos.

        Args:
            hospedaje: Instancia de Hospedaje requerida para validar capacidad.
            reservacion_id: Reservacion a excluir cuando se valida una edicion.
        """

        super().__init__(*args, **kwargs)
        self.hospedaje = hospedaje
        self.reservacion_id = reservacion_id

   # ------------------------------------------------------------------
    # Validaciones individuales de campo
    # ------------------------------------------------------------------

    def clean_fecha_inicio(self):
        """Rechaza fechas de llegada anteriores al dia actual."""

        fecha_inicio = self.cleaned_data["fecha_inicio"]
        if fecha_inicio < date.today():
            raise forms.ValidationError(
                "La fecha de llegada no puede ser en el pasado."
            )
        return fecha_inicio


    def clean_fecha_fin(self):
        """Rechaza fechas de salida que no sean posteriores a la llegada."""

        fecha_fin = self.cleaned_data["fecha_fin"]
        fecha_inicio = self.cleaned_data.get("fecha_inicio")
        if fecha_inicio is None:
            return fecha_fin  
        if fecha_fin <= fecha_inicio:
            raise forms.ValidationError(
                "La fecha de salida debe ser posterior a la fecha de llegada."
            )
        return fecha_fin

    # ------------------------------------------------------------------
    # Validación cruzada (limpiar datos  generales)
    # ------------------------------------------------------------------

    def clean(self):
        """Aplica validaciones cruzadas de temporada, martes y disponibilidad."""

        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        num_huespedes = cleaned_data.get("num_huespedes")
        unidades_reservadas = cleaned_data.get("unidades_reservadas")

        # Necesitamos ambas fechas para las siguientes validaciones
        if not fecha_inicio or not fecha_fin:
            return cleaned_data

        # 1. Fecha fin posterior a fecha inicio
        if fecha_fin <= fecha_inicio:
            self.add_error(
                "fecha_fin",
                "La fecha de salida debe ser posterior a la fecha de llegada."
            )
            return cleaned_data  # sin fechas válidas no tiene sentido continuar

        # 2. Temporada: solo junio–agosto
        if not fechas_en_temporada(fecha_inicio, fecha_fin):
            self.add_error(
                "fecha_inicio",
                "Las reservaciones solo están disponibles de junio a agosto. "
                "Verifica que toda la estancia caiga dentro de esos meses."
            )

        # 3. Sin martes en la estancia
        if rango_incluye_martes(fecha_inicio, fecha_fin):
            self.add_error(
                "fecha_inicio",
                "La estancia no puede incluir días martes."
            )

        # Las siguientes validaciones requieren hospedaje
        if not self.hospedaje:
            return cleaned_data

        # 4. Calcular unidades necesarias y validar que se reserven suficientes
        if num_huespedes and unidades_reservadas:
            unidades_necesarias = calcular_unidades_necesarias(
                num_huespedes, self.hospedaje.capacidad_unidad
            )
            if unidades_reservadas < unidades_necesarias:
                self.add_error(
                    "unidades_reservadas",
                    f"Para {num_huespedes} huésped(es) necesitas al menos "
                    f"{unidades_necesarias} unidad(es) "
                    f"(capacidad: {self.hospedaje.capacidad_unidad} por unidad)."
                )

        # 5. Validar disponibilidad real (evitar sobre-reservaciones)
        if unidades_reservadas:
            disponibles = unidades_disponibles(
                self.hospedaje, fecha_inicio, fecha_fin, self.reservacion_id
            )
            if unidades_reservadas > disponibles:
                self.add_error(
                    "unidades_reservadas",
                    f"Solo quedan {disponibles} unidad(es) disponible(s) "
                    f"para ese periodo en este hospedaje."
                )

        return cleaned_data
    
    def calcular_precio(self):
        """Retorna el precio total si el formulario es valido."""

        if not self.is_valid():
            return None
        d = self.cleaned_data
        num_noches = (d["fecha_fin"] - d["fecha_inicio"]).days
        return calcular_precio_total(
            unidades_reservadas=d["unidades_reservadas"],
            precio_por_unidad=self.hospedaje.precio_por_unidad,
            num_noches=num_noches,
        )
