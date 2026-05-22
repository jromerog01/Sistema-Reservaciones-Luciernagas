from parques.mapa_adapters import OpenStreetMapAdapter
from parques.models import Parque


class MapaService:
    def __init__(self, mapa_adapter=None):
        self.mapa_adapter = mapa_adapter or OpenStreetMapAdapter()

    def obtener_marcadores(self):
        parques = (
            Parque.objects
            .prefetch_related("servicios", "hospedajes")
            .order_by("nombre")
        )
        return self.mapa_adapter.generar_marcadores(parques)
