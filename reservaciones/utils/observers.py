from abc import ABC, abstractmethod

from django.core.mail import send_mail


class ReservacionObserver(ABC):
    """Interfaz que deben implementar todos los observadores de reservaciones."""

    @abstractmethod
    def update(self, evento: str, reservacion) -> None:
        """
        Recibe la notificación de un evento.

        :param evento: Nombre de evento, ej. 'creada', 'cancelada'
        :param reservacion: Instancia de Reservacion afectada
        """
        pass


class CorreoConfirmacionObserver(ReservacionObserver):
    """Envía un correo de confirmación cuando se crea una reservación."""

    def update(self, evento: str, reservacion) -> None:
        if evento != "creada":
            return

        usuario = reservacion.usuario
        hospedaje = reservacion.hospedaje
        parque = hospedaje.parque
        duracion = reservacion.calcular_duracion()

        asunto = f"✅ Confirmación de tu reservación #{reservacion.id} – Luciérnagas"

        mensaje = (
            f"Hola {usuario.get_full_name() or usuario.username},\n\n"
            f"Tu reservación ha sido confirmada exitosamente. Aquí están los detalles:\n\n"
            f"  📋 Número de reservación : #{reservacion.id}\n"
            f"  🏕️  Hospedaje              : {hospedaje.get_tipo_hospedaje_display()}\n"
            f"  🌳 Parque                 : {parque.nombre}\n"
            f"  📅 Fecha de entrada       : {reservacion.fecha_inicio.strftime('%d/%m/%Y')}\n"
            f"  📅 Fecha de salida        : {reservacion.fecha_fin.strftime('%d/%m/%Y')}\n"
            f"  🌙 Duración               : {duracion} noche(s)\n"
            f"  👥 Número de huéspedes    : {reservacion.num_huespedes}\n"
            f"  🏠 Unidades reservadas    : {reservacion.unidades_reservadas}\n"
            f"  💰 Precio total           : ${reservacion.precio_total} MXN\n\n"
            f"Si tienes alguna pregunta o necesitas modificar tu reservación, "
            f"no dudes en contactarnos.\n\n"
            f"¡Esperamos verte pronto!\n"
            f"El equipo de Luciérnagas 🌟"
        )

        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=None,
            recipient_list=[usuario.email],
            fail_silently=True,
        )


class CorreoCancelacionObserver(ReservacionObserver):
    """Envía un correo de aviso cuando se cancela una reservación."""

    def update(self, evento: str, reservacion) -> None:
        if evento != "cancelada":
            return

        usuario = reservacion.usuario
        hospedaje = reservacion.hospedaje

        asunto = f"❌ Tu reservación #{reservacion.id} ha sido cancelada – Luciérnagas"

        mensaje = (
            f"Hola {usuario.get_full_name() or usuario.username},\n\n"
            f"Te confirmamos que tu reservación ha sido cancelada:\n\n"
            f"  📋 Número de reservación : #{reservacion.id}\n"
            f"  🏕️  Hospedaje              : {hospedaje.get_tipo_hospedaje_display()}\n"
            f"  📅 Fecha de entrada       : {reservacion.fecha_inicio.strftime('%d/%m/%Y')}\n"
            f"  📅 Fecha de salida        : {reservacion.fecha_fin.strftime('%d/%m/%Y')}\n\n"
            f"Si esto fue un error o tienes alguna duda, contáctanos.\n\n"
            f"El equipo de Luciérnagas 🌟"
        )

        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=None,
            recipient_list=[usuario.email],
            fail_silently=True,
        )