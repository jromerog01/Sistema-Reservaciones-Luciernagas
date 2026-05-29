from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from parques.models import Hospedaje
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion
from reservaciones.utils.notificador import notificador
from reservaciones.facade import ReservacionFacade
from parques.parque_cards import obtener_imagen_parque


def render_reservacion_forbidden(request, mensaje):
    """Renderiza una respuesta 403 consistente para accesos no autorizados."""
    return render(
        request,
        "acceso_denegado_reservacion.html",
        {"mensaje": mensaje},
        status=403,
    )


def crear_reservacion(request, hospedaje_id):
    """Crea una reservacion para el hospedaje seleccionado por el cliente."""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('usuarios:login')}?next={request.get_full_path()}")


    hospedaje = get_object_or_404(Hospedaje.objects.select_related("parque"), id=hospedaje_id)

    if request.method == "POST":
        form = ReservacionForm(request.POST, hospedaje=hospedaje)
        if form.is_valid():
            reservacion = ReservacionFacade.crear_reservacion(request, hospedaje, form)
            if reservacion:
                return redirect("detalle_reservacion", reservacion_id=reservacion.id)
    else:
        form = ReservacionForm(hospedaje=hospedaje)


    return render(
        request,
        "crear_reservacion.html",
        {"form": form, "hospedaje": hospedaje},
    )


@login_required(login_url="usuarios:login")
def cancelar_reservacion(request, reservacion_id):
    """Cancela una reservacion si el solicitante es propietario o administrador."""
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("hospedaje__parque", "usuario"),
        id=reservacion_id,
    )

    # Delegar la verificación y la acción al facade
    if request.method == "POST":
        success, reason = ReservacionFacade.cancelar_reservacion(reservacion, request.user)
        if not success:
            if reason == "permiso":
                return render_reservacion_forbidden(
                    request,
                    "No tienes permiso para cancelar esta reservación.",
                )
            if reason == "estado":
                return render(
                    request,
                    "cancelar_reservacion.html",
                    {
                        "reservacion": reservacion,
                        "error": "Solo se pueden cancelar reservaciones activas.",
                        "imagen_parque": obtener_imagen_parque(reservacion.hospedaje.parque),
                    },
                )

        return redirect("mis_reservaciones")

    return render(
        request,
        "cancelar_reservacion.html",
        {"reservacion": reservacion, "imagen_parque": obtener_imagen_parque(reservacion.hospedaje.parque)},
    )

@login_required(login_url="usuarios:login")
def mis_reservaciones(request):
    """Lista las reservaciones del usuario autenticado."""
    reservaciones = (
        Reservacion.objects
        .filter(usuario=request.user)
        .select_related("hospedaje__parque")
        .order_by("-fecha_creacion")
    )
    return render(
        request,
        "mis_reservaciones.html",
        {"reservaciones": reservaciones},
    )


@login_required(login_url="usuarios:login")
def detalle_reservacion(request, reservacion_id):
    """Muestra una reservacion solo a su dueño o a un administrador."""
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("hospedaje__parque", "usuario"),
        id=reservacion_id,
    )

    es_propietario = reservacion.usuario == request.user
    es_admin = request.user.es_administrador()

    if not es_propietario and not es_admin:
        return render_reservacion_forbidden(
            request,
            "No tienes permiso para ver esta reservación.",
        )

    return render(
        request,
        "detalle_reservacion.html",
        {
            "reservacion": reservacion, 
            "duracion": reservacion.calcular_duracion(),
            "imagen_parque": obtener_imagen_parque(reservacion.hospedaje.parque),
        },
    )


@login_required(login_url="usuarios:login")
def todas_las_reservaciones(request):
    """Permite a administradores consultar todas las reservaciones."""
    if not request.user.es_administrador():
        return render_reservacion_forbidden(
            request,
            "Solo los administradores pueden ver todas las reservaciones.",
        )

    reservaciones = (
        Reservacion.objects
        .select_related("hospedaje__parque", "usuario")
        .order_by("-fecha_creacion")
    )
    return render(request, "todas_las_reservaciones.html", {"reservaciones": reservaciones})
