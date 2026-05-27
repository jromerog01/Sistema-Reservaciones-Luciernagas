from parques.mapa_adapters import OpenStreetMapAdapter
from parques.models import Parque


class MapaService:
    """Coordina la consulta de parques y su conversion a marcadores de mapa."""

    def __init__(self, mapa_adapter=None):
        """Permite inyectar otro adapter para cambiar proveedor de mapas."""

        self.mapa_adapter = mapa_adapter or OpenStreetMapAdapter()

    def obtener_marcadores(self):
        """Obtiene parques con relaciones precargadas y devuelve marcadores."""

        parques = (
            Parque.objects
            .prefetch_related("servicios", "hospedajes")
            .order_by("nombre")
        )
        return self.mapa_adapter.generar_marcadores(parques)
