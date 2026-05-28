# reservaciones/notificador.py

from reservaciones.utils.observers import (
    ReservacionObserver,
    CorreoConfirmacionObserver,
    CorreoCancelacionObserver,
)


class ReservacionNotificador:
    """
    Sujeto (Subject) del patrón Observer.
    Mantiene la lista de observadores y los notifica ante eventos de reservaciones.
    """

    def __init__(self):
        self._observers: list[ReservacionObserver] = []

    def agregar_observer(self, observer: ReservacionObserver) -> None:
        """Registra un observador interesado en eventos de reservacion."""
        self._observers.append(observer)

    def remover_observer(self, observer: ReservacionObserver) -> None:
        """Elimina un observador previamente registrado."""
        self._observers.remove(observer)

    def notificar(self, evento: str, reservacion) -> None:
        """Propaga el evento a todos los observadores registrados."""
        for observer in self._observers:
            observer.update(evento, reservacion)


# ── Instancia global preconfigurada con los observadores por defecto ─────────
# Se crea una sola vez y se reutiliza en todas las vistas.

notificador = ReservacionNotificador()
notificador.agregar_observer(CorreoConfirmacionObserver())
notificador.agregar_observer(CorreoCancelacionObserver())
