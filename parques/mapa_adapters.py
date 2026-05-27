from abc import ABC, abstractmethod

from django.urls import reverse
from django.utils.text import slugify


DESCRIPCION_PARQUE_DEFAULT = (
    "Parque registrado para consulta de disponibilidad y hospedaje durante la temporada."
)


class MapaAdapter(ABC):
    """Interfaz comun para adaptar parques a proveedores de mapas."""

    @abstractmethod
    def convertir_parque_a_marcador(self, parque):
        """Convierte un parque en la estructura esperada por el mapa."""

        pass

    def generar_marcadores(self, parques):
        """Convierte una coleccion de parques en marcadores."""

        return [
            self.convertir_parque_a_marcador(parque)
            for parque in parques
        ]

    def obtener_servicios(self, parque):
        """Devuelve los nombres de servicios del parque."""

        return [
            servicio.nombre
            for servicio in parque.obtener_servicios()
        ]

    def obtener_hospedajes(self, parque):
        """Devuelve las etiquetas visibles de hospedajes del parque."""

        return [
            hospedaje.get_tipo_hospedaje_display()
            for hospedaje in parque.obtener_hospedajes()
        ]

    def obtener_hospedajes_valores(self, parque):
        """Devuelve valores normalizados para filtrar por tipo de hospedaje."""

        return [
            hospedaje.tipo_hospedaje.lower()
            for hospedaje in parque.obtener_hospedajes()
        ]

    def obtener_servicios_valores(self, parque):
        """Devuelve valores normalizados para filtrar por servicio."""

        return [
            slugify(servicio.nombre)
            for servicio in parque.obtener_servicios()
        ]

    def obtener_horario(self, parque):
        """Formatea el horario del parque para mostrarlo en el marcador."""

        return (
            f"{parque.horario_apertura.strftime('%H:%M')} - "
            f"{parque.horario_cierre.strftime('%H:%M')}"
        )


class OpenStreetMapAdapter(MapaAdapter):
    """Adapter para generar marcadores compatibles con Leaflet/OpenStreetMap."""

    def convertir_parque_a_marcador(self, parque):
        return {
            "idParque": parque.id,
            "nombre": parque.nombre,
            "estado": parque.get_estado_display(),
            "estadoValor": parque.estado.lower(),
            "direccion": parque.direccion,
            "descripcion": parque.descripcion or DESCRIPCION_PARQUE_DEFAULT,
            "latitud": float(parque.latitud),
            "longitud": float(parque.longitud),
            "horario": self.obtener_horario(parque),
            "servicios": self.obtener_servicios(parque),
            "serviciosValores": self.obtener_servicios_valores(parque),
            "hospedajes": self.obtener_hospedajes(parque),
            "hospedajesValores": self.obtener_hospedajes_valores(parque),
            "url": reverse("detalle_parque", args=[parque.id]),
        }


class GoogleMapsAdapter(MapaAdapter):
    """Adapter alternativo para estructuras compatibles con Google Maps."""

    def convertir_parque_a_marcador(self, parque):
        return {
            "idParque": parque.id,
            "title": parque.nombre,
            "position": {
                "lat": float(parque.latitud),
                "lng": float(parque.longitud),
            },
            "infoWindow": {
                "estado": parque.get_estado_display(),
                "estadoValor": parque.estado.lower(),
                "direccion": parque.direccion,
                "descripcion": parque.descripcion or DESCRIPCION_PARQUE_DEFAULT,
                "horario": self.obtener_horario(parque),
                "servicios": self.obtener_servicios(parque),
                "serviciosValores": self.obtener_servicios_valores(parque),
                "hospedajes": self.obtener_hospedajes(parque),
                "hospedajesValores": self.obtener_hospedajes_valores(parque),
                "url": reverse("detalle_parque", args=[parque.id]),
            },
        }
