from django.shortcuts import render
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


def inicio(request):
    mapa_service = MapaService()

    return render(
        request,
        "pagina_inicio.html",
        {
            "mapa_parques": mapa_service.obtener_marcadores(),
            "parques_carrusel": obtener_parques_con_imagenes(),
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
