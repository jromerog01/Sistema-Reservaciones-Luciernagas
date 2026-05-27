"""Notificador de eventos de reservaciones basado en el patron Observer."""

from reservaciones.utils.observers import (
    ReservacionObserver,
    CorreoConfirmacionObserver,
    CorreoCancelacionObserver,
)


class ReservacionNotificador:
    """Sujeto del patron Observer para eventos de reservaciones.

    Mantiene la lista de observadores y los notifica ante eventos de reservaciones.
    """

    def __init__(self):
        """Inicializa el notificador sin observadores registrados."""

        self._observers: list[ReservacionObserver] = []

    def agregar_observer(self, observer: ReservacionObserver) -> None:
        """Registra un observador para recibir eventos de reservacion."""

        self._observers.append(observer)

    def remover_observer(self, observer: ReservacionObserver) -> None:
        """Elimina un observador previamente registrado."""

        self._observers.remove(observer)

    def notificar(self, evento: str, reservacion) -> None:
        """Propaga un evento de reservacion a todos los observadores."""

        for observer in self._observers:
            observer.update(evento, reservacion)


# Instancia compartida por las vistas y preconfigurada con correos por defecto.
notificador = ReservacionNotificador()
notificador.agregar_observer(CorreoConfirmacionObserver())
notificador.agregar_observer(CorreoCancelacionObserver())
