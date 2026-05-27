from django.shortcuts import render
from django.urls import reverse
from django.db.models import Min
from django.utils.text import slugify

from parques.mapa_service import MapaService
from parques.models import Hospedaje, Parque, Servicio
from parques.parque_cards import obtener_parques_con_imagenes


def formatear_precio(precio):
    if precio is None:
        return "no disponible"

    if precio == precio.to_integral_value():
        return f"${precio:,.0f} MXN"

    return f"${precio:,.2f} MXN"


def obtener_minimos_hospedaje_por_estado():
    minimos = {}

    for estado, _ in Parque.Estado.choices:
        estado_key = estado.lower()
        minimos[estado_key] = {}

        for tipo, _ in Hospedaje.TipoHospedaje.choices:
            tipo_key = tipo.lower()
            valores = Hospedaje.objects.filter(
                parque__estado=estado,
                tipo_hospedaje=tipo,
            ).aggregate(
                precio=Min("precio_por_unidad"),
                capacidad=Min("capacidad_unidad"),
                unidades=Min("cantidad_unidades"),
            )

            minimos[estado_key][tipo_key] = {
                "precio": formatear_precio(valores["precio"]),
                "capacidad": valores["capacidad"],
                "unidades": valores["unidades"],
                "unidadDisponible": "espacios" if tipo == Hospedaje.TipoHospedaje.CAMPING else "unidades",
            }

    return minimos


def obtener_servicios_para_filtros():
    return [
        {
            "nombre": servicio.nombre,
            "valor": slugify(servicio.nombre),
        }
        for servicio in Servicio.objects.order_by("nombre")
    ]


def obtener_estados_disponibles():
    return [
        (valor.lower(), etiqueta)
        for valor, etiqueta in Parque.Estado.choices
    ]


def obtener_parques_reservables():
    parques_reservables = []

    for parque in Parque.objects.prefetch_related("hospedajes").order_by("nombre"):
        hospedajes = []

        for hospedaje in parque.hospedajes.all():
            hospedajes.append(
                {
                    "id": hospedaje.id,
                    "tipo": hospedaje.get_tipo_hospedaje_display(),
                    "tipo_valor": hospedaje.tipo_hospedaje.lower(),
                    "cantidad_unidades": hospedaje.cantidad_unidades,
                    "capacidad_unidad": hospedaje.capacidad_unidad,
                    "precio_por_unidad": hospedaje.precio_por_unidad,
                    "url": reverse("crear_reservacion", args=[hospedaje.id]),
                }
            )

        if hospedajes:
            parques_reservables.append(
                {
                    "id": parque.id,
                    "nombre": parque.nombre,
                    "estado": parque.get_estado_display(),
                    "estado_valor": parque.estado.lower(),
                    "descripcion": parque.descripcion,
                    "hospedajes": hospedajes,
                }
            )

    return parques_reservables



def inicio(request):
    mapa_service = MapaService()

    return render(
        request,
        "pagina_inicio.html",
        {
            "estados_hospedaje": obtener_estados_disponibles(),
            "mapa_parques": mapa_service.obtener_marcadores(),
            "parques_carrusel": obtener_parques_con_imagenes(),
            "parques_reservables": obtener_parques_reservables(),
            "minimos_hospedaje": obtener_minimos_hospedaje_por_estado(),
        },
    )


def mapa(request):
    mapa_service = MapaService()

    return render(
        request,
        "mapa_parques.html",
        {
            "mapa_parques": mapa_service.obtener_marcadores(),
            "estados": Parque.Estado.choices,
            "hospedajes": Hospedaje.TipoHospedaje.choices,
            "servicios": obtener_servicios_para_filtros(),
        },
    )
