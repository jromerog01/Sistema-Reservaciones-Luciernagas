import hashlib
import random

from django.utils.text import slugify
from django.templatetags.static import static

from parques.models import Hospedaje, Parque


BOSQUE_IMAGES = [
    f"img/bosque/bosque{index}.jpg"
    for index in range(1, 16)
]

BOSQUE_IMAGES_BY_PARK_ID = {
    9: "img/bosque/bosque13.jpg",
    8: "img/bosque/bosque14.jpg",
    2: "img/bosque/bosque11.jpg",
    10: "img/bosque/bosque15.jpg",
}

GALLERY_IMAGES = {
    "bosque": BOSQUE_IMAGES,
    "cabana": [
        f"img/cabana/cabana{index}.jpg"
        for index in range(1, 7)
    ] + [
        "img/cabana/cabana8.jpg",
    ],
    "camping": [
        f"img/camping/camping{index}.jpg"
        for index in range(1, 7)
    ] + [
        "img/camping/fogata1.jpg",
        "img/camping/fogata2.jpg",
    ],
    "rios": [
        f"img/rios/cascada{index}.jpg"
        for index in range(1, 7)
    ] + [
        f"img/rios/rio{index}.jpg"
        for index in range(1, 6)
    ],
}

REQUIRED_GALLERY_IMAGES = {
    "camping": [
        f"img/camping/camping{index}.jpg"
        for index in range(1, 7)
    ],
}


def crear_generador_parque(parque, namespace):
    """Crea un generador pseudoaleatorio estable para un parque."""
    seed = f"{namespace}:{parque.id}:{parque.nombre}".encode()
    seed_number = int(hashlib.sha256(seed).hexdigest(), 16)
    return random.Random(seed_number)


def obtener_ruta_imagen_bosque(index, parque_id=None):
    """Devuelve una imagen local estable para la imagen principal del parque."""
    if parque_id in BOSQUE_IMAGES_BY_PARK_ID:
        return BOSQUE_IMAGES_BY_PARK_ID[parque_id]

    return BOSQUE_IMAGES[index % len(BOSQUE_IMAGES)]


def obtener_imagen_bosque(index, parque_id=None):
    """Devuelve la URL estatica de la imagen principal del parque."""
    return static(obtener_ruta_imagen_bosque(index, parque_id))


def obtener_imagen_parque(parque):
    """Asigna una imagen principal local y estable segun el orden alfabetico."""
    parques_ids = Parque.objects.order_by("nombre").values_list("id", flat=True)

    for index, parque_id in enumerate(parques_ids):
        if parque_id == parque.id:
            return obtener_imagen_bosque(index, parque.id)

    return obtener_imagen_bosque(0, parque.id)


def obtener_galeria_parque(parque, total=5):
    """Genera una galeria local, pseudoaleatoria y estable para el parque."""
    parques_ids = list(Parque.objects.order_by("nombre").values_list("id", flat=True))
    try:
        parque_index = parques_ids.index(parque.id)
    except ValueError:
        parque_index = 0
    
    todas_principales = {
        obtener_ruta_imagen_bosque(idx, p_id)
        for idx, p_id in enumerate(parques_ids)
    }

    tipos_hospedaje = set(parque.hospedajes.values_list("tipo_hospedaje", flat=True))
    categorias = ["bosque", "rios"]

    if Hospedaje.TipoHospedaje.CAMPING in tipos_hospedaje:
        categorias.append("camping")

    if Hospedaje.TipoHospedaje.CABANA in tipos_hospedaje:
        categorias.append("cabana")

    generator = crear_generador_parque(parque, "galeria")
    seleccionadas = []

    for categoria in categorias:
        imagenes_categoria = REQUIRED_GALLERY_IMAGES.get(categoria, GALLERY_IMAGES[categoria])
        opciones = [
            imagen
            for imagen in imagenes_categoria
            if imagen not in todas_principales and imagen not in seleccionadas
        ]

        if opciones:
            if categoria == "rios":
                # Mezclamos la lista de ríos con una semilla fija para intercalar perfectamente cascadas y ríos.
                # Luego rotamos basándonos en el índice del parque.
                mezclador = random.Random("mezcla_rios_estable")
                mezclador.shuffle(opciones)
                seleccionada = opciones[parque_index % len(opciones)]
                seleccionadas.append(seleccionada)
            else:
                seleccionadas.append(generator.choice(opciones))

    minimo_total = max(total, len(seleccionadas))
    restantes = [
        imagen
        for categoria in categorias
        for imagen in GALLERY_IMAGES[categoria]
        if imagen not in todas_principales and imagen not in seleccionadas
    ]
    generator.shuffle(restantes)
    seleccionadas.extend(restantes[:max(0, minimo_total - len(seleccionadas))])

    return [
        static(imagen)
        for imagen in seleccionadas[:minimo_total]
    ]


def obtener_parques_con_imagenes():
    """Prepara los parques con imagen y valores de filtro para listados visuales."""
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
            "imagen": obtener_imagen_bosque(index, parque.id),
            "filtros": {
                "estado": parque.estado.lower(),
                "hospedajes": " ".join(hospedajes),
                "servicios": " ".join(servicios),
            },
        })
    return parques
