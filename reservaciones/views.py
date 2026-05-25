from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from urllib.parse import urlencode

from parques.models import Hospedaje
from django.db.models import Sum
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion
from reservaciones.utils.template_method import ReservacionHospedajeTemplate


def crear_reservacion(request, hospedaje_id):
    if not request.user.is_authenticated:
        qs = urlencode({"next": request.get_full_path()})
        login_url = settings.LOGIN_URL
        return redirect(f"{login_url}?{qs}")

    hospedaje = get_object_or_404(Hospedaje.objects.select_related("parque"), id=hospedaje_id)

    if request.method == "POST":
        form = ReservacionForm(request.POST)
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


@login_required
def cancelar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("hospedaje__parque", "usuario"),
        id=reservacion_id,
    )

    es_propietario = reservacion.usuario == request.user
    es_admin = request.user.es_administrador()

    if not es_propietario and not es_admin:
        return HttpResponseForbidden("No tienes permiso para cancelar esta reservación.")

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
        return redirect("mis_reservaciones")

    return render(
        request,
        "cancelar_reservacion.html",
        {"reservacion": reservacion},
    )

@login_required
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


@login_required
def detalle_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(
        Reservacion.objects.select_related("hospedaje__parque", "usuario"),
        id=reservacion_id,
    )

    es_propietario = reservacion.usuario == request.user
    es_admin = request.user.es_administrador()

    if not es_propietario and not es_admin:
        return HttpResponseForbidden("No tienes permiso para ver esta reservación.")

    return render(
        request,
        "detalle_reservacion.html",
        {"reservacion": reservacion, "duracion": reservacion.calcular_duracion()},
    )


