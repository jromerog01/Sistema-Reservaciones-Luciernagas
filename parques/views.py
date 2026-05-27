from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify

from parques.parque_cards import obtener_galeria_parque, obtener_imagen_parque, obtener_parques_con_imagenes
from parques.models import Hospedaje, Parque, Servicio


def listado_parques(request):
    servicios = [
        {
            "nombre": servicio.nombre,
            "valor": slugify(servicio.nombre),
        }
        for servicio in Servicio.objects.order_by("nombre")
    ]

    return render(
        request,
        "listado_parques.html",
        {
            "parques": obtener_parques_con_imagenes(),
            "estados": Parque.Estado.choices,
            "hospedajes": Hospedaje.TipoHospedaje.choices,
            "servicios": servicios,
        },
    )


def detalle_parque(request, parque_id):
    parque = get_object_or_404(
        Parque.objects.prefetch_related("servicios", "hospedajes"),
        id=parque_id,
    )

    return render(
        request,
        "detalle_parque.html",
        {
            "parque": parque,
            "imagen": obtener_imagen_parque(parque),
            "galeria": obtener_galeria_parque(parque),
        },
    )
