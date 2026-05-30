from typing import Tuple, Type, Dict

from django.core.exceptions import PermissionDenied

from reservaciones.utils.template_method import ReservacionHospedajeTemplate
from reservaciones.utils.notificador import notificador
from reservaciones.models import Reservacion

# Registro de templates para diferentes tipos de reservación.
# La clave por defecto es el nombre en minúsculas de la clase del recurso
# (por ejemplo: 'hospedaje', 'restaurante'). Se puede ampliar mediante
# `register_template` si se añaden nuevos tipos.
_TEMPLATE_REGISTRY: Dict[str, Type] = {
    "hospedaje": ReservacionHospedajeTemplate,
}


def register_template(key: str, template_class: Type):
    """Registra una clase template bajo `key` para que la fachada la use.

    Uso: `register_template('restaurante', ReservacionRestauranteTemplate)`
    """
    _TEMPLATE_REGISTRY[key.lower()] = template_class


class ReservacionFacade:
    """Fachada que centraliza operaciones de alto nivel sobre reservaciones.

    Encapsula el uso del Template Method, la notificación y las reglas de
    cancelación para que las vistas llamen a una API limpia y coherente.
    """

    @staticmethod
    def crear_reservacion(request, recurso, form, template_class: Type = None):
        """Crea una reservación usando el Template Method y devuelve la instancia.

        Retorna la instancia `Reservacion` si se creó correctamente o `None`
        si el formulario no es válido o falló alguna validación del template.
        """
        # Si se recibe una clase explícita, usarla.
        if template_class is not None:
            processor_cls = template_class
        else:
            # intentar determinar la clave a partir del objeto `recurso`.
            # Preferir un atributo `tipo` si existe, sino el nombre de la clase.
            tipo = getattr(recurso, "tipo", None)
            if tipo:
                key = str(tipo).lower()
            else:
                key = recurso.__class__.__name__.lower()

            processor_cls = _TEMPLATE_REGISTRY.get(key, None)

            # Si no hay plantilla registrada para ese tipo, caer a la
            # implementación por defecto para hospedaje.
            if processor_cls is None:
                processor_cls = ReservacionHospedajeTemplate

        processor = processor_cls(request, recurso, form)
        return processor.procesar_reservacion()

    @staticmethod
    def puede_cancelar(reservacion: Reservacion, usuario) -> bool:
        """Indica si `usuario` puede cancelar `reservacion`.

        Centraliza la regla de propiedad/administración para reutilización.
        """
        return reservacion.usuario == usuario or usuario.es_administrador()

    @staticmethod
    def cancelar_reservacion(reservacion: Reservacion, usuario) -> Tuple[bool, str | None]:
        """Intenta cancelar la reservación.

        Retorna `(True, None)` si la cancelación fue exitosa.
        Si no se permite, retorna `(False, 'permiso')`.
        Si la reservación no está en estado cancelable, retorna
        `(False, 'estado')`.
        """
        if not ReservacionFacade.puede_cancelar(reservacion, usuario):
            return False, "permiso"

        if reservacion.estado != Reservacion.EstadoReservacion.ACTIVA:
            return False, "estado"

        reservacion.estado = Reservacion.EstadoReservacion.CANCELADA
        reservacion.save()

        notificador.notificar("cancelada", reservacion)

        return True, None
