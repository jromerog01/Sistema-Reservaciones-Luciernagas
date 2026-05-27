from django.utils.text import slugify

from parques.models import Parque


# Imagenes externas usadas como fallback visual para las tarjetas de parques.
UNSPLASH_IMAGES = [
    "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1473773508845-188df298d2d1?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1200&q=80",
]


def obtener_imagen_parque(parque):
    """Asigna una imagen estable a un parque segun su posicion alfabetica."""

    parques_ids = Parque.objects.order_by("nombre").values_list("id", flat=True)

    for index, parque_id in enumerate(parques_ids):
        if parque_id == parque.id:
            return UNSPLASH_IMAGES[index % len(UNSPLASH_IMAGES)]

    return UNSPLASH_IMAGES[0]


def obtener_parques_con_imagenes():
    """Devuelve parques con imagen y valores normalizados para filtros de UI."""

    parques = []
    for index, parque in enumerate(
        Parque.objects.prefetch_related("servicios", "hospedajes").order_by("nombre")
    ):
        servicios = [
            slugify(servicio.nombre)
            for servicio in parque.servicios.all()
        ]
        hospedajes = [
            hospedaje.tipo_hospedaje.lower()
            for hospedaje in parque.hospedajes.all()
        ]

        parques.append({
            "parque": parque,
            "imagen": UNSPLASH_IMAGES[index % len(UNSPLASH_IMAGES)],
            "filtros": {
                "estado": parque.estado.lower(),
                "hospedajes": " ".join(hospedajes),
                "servicios": " ".join(servicios),
            },
        })
    return parques
