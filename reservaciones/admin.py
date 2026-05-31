from django.contrib import admin
from django.utils.html import format_html

from reservaciones.models import Reservacion


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    """Configuracion del panel administrativo para auditar reservaciones."""

    list_display = (
        "id",
        "cliente_nombre",
        "correo_cliente",
        "parque_nombre",
        "tipo_hospedaje",
        "fecha_inicio",
        "fecha_fin",
        "num_huespedes",
        "unidades_reservadas",
        "precio_total",
        "estado_badge",
        "fecha_creacion",
    )

    list_filter = (
        "estado",
        "hospedaje__tipo_hospedaje",
        "hospedaje__parque",
        "fecha_inicio",
    )

    search_fields = (
        "usuario__username",
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "hospedaje__parque__nombre",
    )

    readonly_fields = (
        "correo_cliente",
        "fecha_creacion",
    )

    ordering = ("-fecha_creacion",)

    date_hierarchy = "fecha_inicio"

    fieldsets = (
        ("Estancia", {
            "fields": (
                "hospedaje",
                "fecha_inicio",
                "fecha_fin",
                "num_huespedes",
                "unidades_reservadas",
                "precio_total",
            ),
        }),
        ("Cliente", {
            "fields": ("usuario", "correo_cliente"),
        }),
        ("Estado", {
            "fields": ("estado", "fecha_creacion"),
        }),
    )


    @admin.display(description="Parque", ordering="hospedaje__parque__nombre")
    def parque_nombre(self, obj):
        """Expone el parque sin duplicar el dato en Reservacion."""
        return obj.hospedaje.parque.nombre

    @admin.display(description="Hospedaje", ordering="hospedaje__tipo_hospedaje")
    def tipo_hospedaje(self, obj):
        """Muestra la etiqueta legible del tipo de hospedaje reservado."""
        return obj.hospedaje.get_tipo_hospedaje_display()

    @admin.display(description="Cliente", ordering="usuario__username")
    def cliente_nombre(self, obj):
        """Muestra nombre completo o username sin repetir el correo."""
        return obj.usuario.get_full_name() or obj.usuario.username

    @admin.display(description="Correo cliente", ordering="usuario__email")
    def correo_cliente(self, obj):
        """Muestra el correo del cliente asociado a la reservacion."""
        return obj.usuario.email or "-"

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        """Colorea el estado para facilitar lectura en listados largos."""
        colores = {
            Reservacion.EstadoReservacion.ACTIVA:     "#16a34a",   # verde
            Reservacion.EstadoReservacion.CANCELADA:  "#dc2626",   # rojo
            Reservacion.EstadoReservacion.FINALIZADA: "#6b7280",   # gris
        }
        color = colores.get(obj.estado, "#6b7280")
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color,
            obj.get_estado_display(),
        )
