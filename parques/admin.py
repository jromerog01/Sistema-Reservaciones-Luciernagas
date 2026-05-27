from django.contrib import admin
from django import forms

from parques.models import Parque, Servicio, Hospedaje


def get_selected_values(value):
    """Convierte el parametro CSV de un filtro en una lista de valores."""

    if not value:
        return []

    return [selected_value for selected_value in value.split(",") if selected_value]


def build_multiselect_choices(changelist, parameter_name, selected_values, options):
    """Construye opciones de filtro que permiten seleccionar varios valores."""

    yield {
        "selected": not selected_values,
        "query_string": changelist.get_query_string(remove=[parameter_name]),
        "display": "Todos",
    }

    for option_value, option_label in options:
        option_value = str(option_value)
        new_selected_values = selected_values.copy()

        if option_value in new_selected_values:
            new_selected_values.remove(option_value)
        else:
            new_selected_values.append(option_value)

        if new_selected_values:
            query_string = changelist.get_query_string(
                {parameter_name: ",".join(new_selected_values)},
                remove=[],
            )
        else:
            query_string = changelist.get_query_string(remove=[parameter_name])

        yield {
            "selected": option_value in selected_values,
            "query_string": query_string,
            "display": option_label,
        }


class EstadoParqueFilter(admin.SimpleListFilter):
    """Filtro multi-seleccion para consultar parques por estado."""

    title = "estado"
    parameter_name = "estado"

    def lookups(self, request, model_admin):
        """Devuelve los estados disponibles como opciones del filtro."""

        return Parque.Estado.choices

    def queryset(self, request, queryset):
        """Filtra parques por los estados seleccionados en el admin."""

        estados = self._get_estados()

        if estados:
            return queryset.filter(estado__in=estados)

        return queryset

    def choices(self, changelist):
        """Renderiza opciones compatibles con seleccion multiple."""

        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_estados(),
            Parque.Estado.choices,
        )

    def _get_estados(self):
        """Obtiene estados seleccionados y descarta valores no validos."""

        estados_validos = [estado[0] for estado in Parque.Estado.choices]

        return [
            estado
            for estado in get_selected_values(self.value())
            if estado in estados_validos
        ]


class TipoHospedajeParqueFilter(admin.SimpleListFilter):
    """Filtro multi-seleccion para parques que ofrecen tipos de hospedaje."""

    title = "tipo de hospedaje"
    parameter_name = "tipo_hospedaje"

    def lookups(self, request, model_admin):
        """Devuelve los tipos de hospedaje disponibles para filtrar."""

        return (
            (Hospedaje.TipoHospedaje.CABANA, "Cabañas"),
            (Hospedaje.TipoHospedaje.CAMPING, "Camping"),
        )

    def queryset(self, request, queryset):
        """Filtra parques que tengan todos los tipos de hospedaje seleccionados."""

        tipos_hospedaje = self._get_tipos_hospedaje()

        for tipo_hospedaje in tipos_hospedaje:
            queryset = queryset.filter(hospedajes__tipo_hospedaje=tipo_hospedaje)

        return queryset.distinct()

    def choices(self, changelist):
        """Renderiza opciones de hospedaje compatibles con seleccion multiple."""

        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_tipos_hospedaje(),
            self.lookups(None, None),
        )

    def _get_tipos_hospedaje(self):
        """Obtiene tipos seleccionados y descarta valores no validos."""

        tipos_validos = [tipo[0] for tipo in Hospedaje.TipoHospedaje.choices]

        return [
            tipo_hospedaje
            for tipo_hospedaje in get_selected_values(self.value())
            if tipo_hospedaje in tipos_validos
        ]


class ServiciosParqueFilter(admin.SimpleListFilter):
    """Filtro multi-seleccion para parques que cuentan con servicios concretos."""

    title = "servicios"
    parameter_name = "servicios"

    def lookups(self, request, model_admin):
        """Devuelve los servicios registrados como opciones del filtro."""

        return Servicio.objects.values_list("id", "nombre")

    def queryset(self, request, queryset):
        """Filtra parques que cuenten con todos los servicios seleccionados."""

        servicios_ids = self._get_servicios_ids()

        for servicio_id in servicios_ids:
            queryset = queryset.filter(servicios__id=servicio_id)

        return queryset.distinct()

    def choices(self, changelist):
        """Renderiza opciones de servicios compatibles con seleccion multiple."""

        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_servicios_ids(),
            Servicio.objects.order_by("nombre").values_list("id", "nombre"),
        )

    def _get_servicios_ids(self):
        """Obtiene IDs de servicios seleccionados y descarta valores invalidos."""

        return [
            servicio_id
            for servicio_id in get_selected_values(self.value())
            if servicio_id.isdigit()
        ]


class ParqueAdminForm(forms.ModelForm):
    """Formulario admin que obliga a definir la disponibilidad de camping."""

    cantidad_lugares_camping = forms.IntegerField(
        label="Cantidad de lugares de camping",
        min_value=1,
        required=True,
    )
    capacidad_por_lugar_camping = forms.IntegerField(
        label="Capacidad por lugar de camping",
        min_value=1,
        required=True,
    )
    precio_por_lugar_camping = forms.DecimalField(
        label="Precio por lugar de camping",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        required=True,
    )

    class Meta:
        model = Parque
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Carga valores iniciales del hospedaje de camping existente."""

        super().__init__(*args, **kwargs)

        if self.instance.pk:
            hospedaje_camping = self.instance.hospedajes.filter(
                tipo_hospedaje=Hospedaje.TipoHospedaje.CAMPING
            ).first()

            if hospedaje_camping:
                self.fields["cantidad_lugares_camping"].initial = hospedaje_camping.cantidad_unidades
                self.fields["capacidad_por_lugar_camping"].initial = hospedaje_camping.capacidad_unidad
                self.fields["precio_por_lugar_camping"].initial = hospedaje_camping.precio_por_unidad

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    """Administrador de servicios disponibles en los parques."""

    list_display = ("nombre",)
    # list_editable = ("nombre",)
    search_fields = ("nombre",)
    list_per_page = 20
    # readonly_fields = ("id",)
    # ordering = ("id",)



@admin.register(Parque)
class ParqueAdmin(admin.ModelAdmin):
    """Administrador de parques oficiales del festival."""

    form = ParqueAdminForm
    list_display = ("nombre", "estado", "direccion", "latitud", "longitud", "horario_apertura", "horario_cierre", "ver_servicios")
    list_filter = (EstadoParqueFilter, TipoHospedajeParqueFilter, ServiciosParqueFilter)
    search_fields = ("nombre", "direccion", "servicios__nombre")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Muestra servicios como casillas para facilitar la captura."""

        if db_field.name == "servicios":
            kwargs["widget"] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def ver_servicios(self, obj):
        """Devuelve los servicios del parque para la tabla del admin."""

        return ", ".join(servicio.nombre for servicio in obj.servicios.all())

    ver_servicios.short_description = "Servicios"

    def save_model(self, request, obj, form, change):
        """Guarda el parque y asegura que siempre tenga hospedaje de camping."""

        super().save_model(request, obj, form, change)

        hospedaje_camping, created = Hospedaje.objects.get_or_create(
            parque=obj,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CAMPING,
            defaults={
                "cantidad_unidades": form.cleaned_data["cantidad_lugares_camping"],
                "capacidad_unidad": form.cleaned_data["capacidad_por_lugar_camping"],
                "precio_por_unidad": form.cleaned_data["precio_por_lugar_camping"],
            },
        )

        if not created:
            hospedaje_camping.cantidad_unidades = form.cleaned_data["cantidad_lugares_camping"]
            hospedaje_camping.capacidad_unidad = form.cleaned_data["capacidad_por_lugar_camping"]
            hospedaje_camping.precio_por_unidad = form.cleaned_data["precio_por_lugar_camping"]
            hospedaje_camping.save(update_fields=["cantidad_unidades", "capacidad_unidad", "precio_por_unidad"])



@admin.register(Hospedaje)
class HospedajeAdmin(admin.ModelAdmin):
    """Administrador de tipos de hospedaje asociados a cada parque."""

    list_display = ("parque", "tipo_hospedaje", "cantidad_unidades", "capacidad_unidad", "precio_por_unidad")
    list_filter = ("tipo_hospedaje", "parque")
    search_fields = ("parque__nombre",)
