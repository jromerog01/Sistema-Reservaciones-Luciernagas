from parques.mapa_adapters import OpenStreetMapAdapter
from parques.models import Parque


class MapaService:
    """Servicio de lectura para construir los marcadores del mapa interactivo."""

    def __init__(self, mapa_adapter=None):
        # La implementacion del adapter permite cambiar proveedor de mapas sin tocar vistas.
        self.mapa_adapter = mapa_adapter or OpenStreetMapAdapter()

    def obtener_marcadores(self):
        """Obtiene parques con sus relaciones y los adapta para el frontend."""
        parques = (
            Parque.objects
            .prefetch_related("servicios", "hospedajes")
            .order_by("nombre")
        )
        return self.mapa_adapter.generar_marcadores(parques)
