from datetime import date

from django import forms

from reservaciones.models import Reservacion


class ReservacionForm(forms.Form):
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

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            if fecha_inicio < date.today():
                self.add_error("fecha_inicio", "La fecha de llegada no puede ser en el pasado.")
            if fecha_fin <= fecha_inicio:
                self.add_error("fecha_fin", "La fecha de salida debe ser posterior a la fecha de llegada.")

        return cleaned_data
