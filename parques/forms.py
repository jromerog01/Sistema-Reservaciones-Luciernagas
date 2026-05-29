from django.forms import ModelForm

from parques.models import Parque, Servicio, Hospedaje


class ParqueForm(ModelForm):
    """Formulario base para crear o editar parques."""

    class Meta:
        model = Parque
        fields = "__all__"

class ServicioForm(ModelForm):
    """Formulario base para crear o editar servicios."""

    class Meta:
        model = Servicio
        fields = "__all__"


class HospedajeForm(ModelForm):
    """Formulario base para administrar tipos de hospedaje por parque."""

    class Meta:
        model = Hospedaje
        fields = "__all__"
