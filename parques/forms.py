from django.forms import ModelForm

from parques.models import Parque, Servicio, Hospedaje


class ParqueForm(ModelForm):
    class Meta:
        model = Parque
        fields = "__all__"

class ServicioForm(ModelForm):
    class Meta:
        model = Servicio
        fields = "__all__"


class HospedajeForm(ModelForm):
    class Meta:
        model = Hospedaje
        fields = "__all__"
