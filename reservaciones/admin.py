from django.contrib import admin

from reservaciones.models import Reservacion

# Register your models here.

@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
        list_display = ("id", "hospedaje", "usuario", "fecha_inicio", "fecha_fin", "num_huespedes", "unidades_reservadas", "precio_total")
        list_filter = ("hospedaje__parque__nombre", "usuario__username")
        search_fields = ("hospedaje__nombre", "usuario__username")