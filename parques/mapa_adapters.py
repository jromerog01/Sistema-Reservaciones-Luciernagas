from abc import ABC, abstractmethod

from django.urls import reverse
from django.utils.text import slugify


DESCRIPCION_PARQUE_DEFAULT = (
    "Parque registrado para consulta de disponibilidad y hospedaje durante la temporada."
)


class MapaAdapter(ABC):
    @abstractmethod
    def convertir_parque_a_marcador(self, parque):
        pass

    def generar_marcadores(self, parques):
        return [
            self.convertir_parque_a_marcador(parque)
            for parque in parques
        ]

    def obtener_servicios(self, parque):
        return [
            servicio.nombre
            for servicio in parque.obtener_servicios()
        ]

    def obtener_hospedajes(self, parque):
        return [
            hospedaje.get_tipo_hospedaje_display()
            for hospedaje in parque.obtener_hospedajes()
        ]

    def obtener_hospedajes_valores(self, parque):
        return [
            hospedaje.tipo_hospedaje.lower()
            for hospedaje in parque.obtener_hospedajes()
        ]

    def obtener_servicios_valores(self, parque):
        return [
            slugify(servicio.nombre)
            for servicio in parque.obtener_servicios()
        ]

    def obtener_horario(self, parque):
        return (
            f"{parque.horario_apertura.strftime('%H:%M')} - "
            f"{parque.horario_cierre.strftime('%H:%M')}"
        )


class OpenStreetMapAdapter(MapaAdapter):
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
