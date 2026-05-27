from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from parques.models import Hospedaje
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion
from reservaciones.utils.template_method import ReservacionHospedajeTemplate
from reservaciones.utils.notificador import notificador


def render_reservacion_forbidden(request, mensaje):
    return render(
        request,
        "acceso_denegado_reservacion.html",
        {"mensaje": mensaje},
        status=403,
    )


def crear_reservacion(request, hospedaje_id):
    if not request.user.is_authenticated:
        #qs = urlencode({"next": request.get_full_path()})
        #return redirect(f"{reverse('usuarios:login')}?{qs}")
        return redirect(f"{reverse('usuarios:login')}?next={request.get_full_path()}")


    hospedaje = get_object_or_404(Hospedaje.objects.select_related("parque"), id=hospedaje_id)

    if request.method == "POST":
        form = ReservacionForm(request.POST, hospedaje=hospedaje)
        if form.is_valid():
            processor = ReservacionHospedajeTemplate(request, hospedaje, form)
            reservacion = processor.procesar_reservacion()
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
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("hospedaje__parque", "usuario"),
        id=reservacion_id,
    )

    es_propietario = reservacion.usuario == request.user
    es_admin = request.user.es_administrador()

    if not es_propietario and not es_admin:
        return render_reservacion_forbidden(
            request,
            "No tienes permiso para cancelar esta reservación.",
        )

    if request.method == "POST":
        if reservacion.estado != Reservacion.EstadoReservacion.ACTIVA:
            return render(
                request,
                "cancelar_reservacion.html",
                {
                    "reservacion": reservacion,
                    "error": "Solo se pueden cancelar reservaciones activas.",
                },
            )
        reservacion.estado = Reservacion.EstadoReservacion.CANCELADA
        reservacion.save()

        notificador.notificar("cancelada", reservacion)

        return redirect("mis_reservaciones")

    return render(
        request,
        "cancelar_reservacion.html",
        {"reservacion": reservacion},
    )

@login_required(login_url="usuarios:login")
def mis_reservaciones(request):
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
        {"reservacion": reservacion, "duracion": reservacion.calcular_duracion()},
    )


@login_required(login_url="usuarios:login")
def todas_las_reservaciones(request):
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

