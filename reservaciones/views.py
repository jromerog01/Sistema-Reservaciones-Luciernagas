from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from parques.models import Hospedaje
from reservaciones.forms import ReservacionForm
from reservaciones.models import Reservacion


@login_required
def crear_reservacion(request, hospedaje_id):
    hospedaje = get_object_or_404(Hospedaje.objects.select_related("parque"), id=hospedaje_id)

    if request.method == "POST":
        form = ReservacionForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data["fecha_inicio"]
            fecha_fin = form.cleaned_data["fecha_fin"]
            num_huespedes = form.cleaned_data["num_huespedes"]
            unidades_reservadas = form.cleaned_data["unidades_reservadas"]

            errores = []
            
            #Verificar que no se reserven más unidades de las disponibles
            if unidades_reservadas > hospedaje.cantidad_unidades:
                errores.append(
                    f"Solo hay {hospedaje.cantidad_unidades} unidades disponibles para este hospedaje."
                )
            
            #Verificar que el número de huéspedes no exceda la capacidad máxima del hospedaje
            capacidad_maxima = hospedaje.capacidad_unidad * unidades_reservadas
            if num_huespedes > capacidad_maxima:
                errores.append(
                    f"Con {unidades_reservadas} unidad(es) la capacidad máxima es {capacidad_maxima} huéspedes."
                )

            if errores:
                return render(
                    request,
                    "reservaciones/crear_reservacion.html",
                    {"form": form, "hospedaje": hospedaje, "errores": errores},
                )

            duracion = (fecha_fin - fecha_inicio).days
            precio_total = hospedaje.precio_por_unidad * unidades_reservadas * duracion

            reservacion = Reservacion.objects.create(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                num_huespedes=num_huespedes,
                unidades_reservadas=unidades_reservadas,
                precio_total=precio_total,
                hospedaje=hospedaje,
                usuario=request.user,
            )
            return redirect("detalle_reservacion", reservacion_id=reservacion.id)
    else:
        form = ReservacionForm()

    return render(
        request,
        "reservaciones/crear_reservacion.html",
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
                "reservaciones/cancelar_reservacion.html",
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
        "reservaciones/cancelar_reservacion.html",
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
        "reservaciones/mis_reservaciones.html",
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
        "reservaciones/detalle_reservacion.html",
        {"reservacion": reservacion, "duracion": reservacion.calcular_duracion()},
    )
