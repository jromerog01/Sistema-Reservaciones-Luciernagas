from django.contrib import admin
from django import forms

from parques.models import Parque, Servicio, Hospedaje


def get_selected_values(value):
    """Convierte un parametro CSV del admin en lista de valores seleccionados."""
    if not value:
        return []

    return [selected_value for selected_value in value.split(",") if selected_value]


def build_multiselect_choices(changelist, parameter_name, selected_values, options):
    """Construye opciones para filtros de admin con seleccion multiple."""
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
    """Filtro multi-seleccion por estado del parque."""

    title = "estado"
    parameter_name = "estado"

    def lookups(self, request, model_admin):
        """Define las opciones visibles del filtro a partir del enum del modelo."""
        return Parque.Estado.choices

    def queryset(self, request, queryset):
        """Filtra parques por los estados seleccionados en el panel admin."""
        estados = self._get_estados()

        if estados:
            return queryset.filter(estado__in=estados)

        return queryset

    def choices(self, changelist):
        """Renderiza opciones acumulables en lugar del filtro simple de Django."""
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_estados(),
            Parque.Estado.choices,
        )

    def _get_estados(self):
        """Normaliza y descarta estados invalidos recibidos por query string."""
        estados_validos = [estado[0] for estado in Parque.Estado.choices]

        return [
            estado
            for estado in get_selected_values(self.value())
            if estado in estados_validos
        ]


class TipoHospedajeParqueFilter(admin.SimpleListFilter):
    """Filtro multi-seleccion que exige todos los tipos elegidos."""

    title = "tipo de hospedaje"
    parameter_name = "tipo_hospedaje"

    def lookups(self, request, model_admin):
        """Define los tipos de hospedaje disponibles para filtrar parques."""
        return (
            (Hospedaje.TipoHospedaje.CABANA, "Cabañas"),
            (Hospedaje.TipoHospedaje.CAMPING, "Camping"),
        )

    def queryset(self, request, queryset):
        """Filtra parques que tengan todos los hospedajes seleccionados."""
        tipos_hospedaje = self._get_tipos_hospedaje()

        for tipo_hospedaje in tipos_hospedaje:
            queryset = queryset.filter(hospedajes__tipo_hospedaje=tipo_hospedaje)

        return queryset.distinct()

    def choices(self, changelist):
        """Renderiza el filtro como selección multiple acumulable."""
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_tipos_hospedaje(),
            self.lookups(None, None),
        )

    def _get_tipos_hospedaje(self):
        """Normaliza y descarta tipos de hospedaje invalidos."""
        tipos_validos = [tipo[0] for tipo in Hospedaje.TipoHospedaje.choices]

        return [
            tipo_hospedaje
            for tipo_hospedaje in get_selected_values(self.value())
            if tipo_hospedaje in tipos_validos
        ]


class ServiciosParqueFilter(admin.SimpleListFilter):
    """Filtro multi-seleccion que exige todos los servicios elegidos."""

    title = "servicios"
    parameter_name = "servicios"

    def lookups(self, request, model_admin):
        """Carga los servicios registrados como opciones del filtro."""
        return Servicio.objects.values_list("id", "nombre")

    def queryset(self, request, queryset):
        """Filtra parques que contengan todos los servicios seleccionados."""
        servicios_ids = self._get_servicios_ids()

        for servicio_id in servicios_ids:
            queryset = queryset.filter(servicios__id=servicio_id)

        return queryset.distinct()

    def choices(self, changelist):
        """Renderiza servicios como filtro multi-seleccion."""
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_servicios_ids(),
            Servicio.objects.order_by("nombre").values_list("id", "nombre"),
        )

    def _get_servicios_ids(self):
        """Obtiene solo ids numericos para evitar parametros invalidos."""
        return [
            servicio_id
            for servicio_id in get_selected_values(self.value())
            if servicio_id.isdigit()
        ]


class ParqueAdminForm(forms.ModelForm):
    """Formulrio de admin que garantiza camping para todos los parques."""

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
    """Configuracion administrativa de servicios disponibles."""

    list_display = ("nombre",)
    search_fields = ("nombre",)
    list_per_page = 20



@admin.register(Parque)
class ParqueAdmin(admin.ModelAdmin):
    """Panel administrativo para gestionar parques y su camping base."""

    form = ParqueAdminForm
    list_display = ("nombre", "estado", "direccion", "latitud", "longitud", "horario_apertura", "horario_cierre", "ver_servicios")
    list_filter = (EstadoParqueFilter, TipoHospedajeParqueFilter, ServiciosParqueFilter)
    search_fields = ("nombre", "direccion", "servicios__nombre")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Usa checkboxes para que la selección de servicios sea clara."""
        if db_field.name == "servicios":
            kwargs["widget"] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def ver_servicios(self, obj):
        """Muestra servicios asociados en una sola columna del listado."""
        return ", ".join(servicio.nombre for servicio in obj.servicios.all())

    ver_servicios.short_description = "Servicios"

    def save_model(self, request, obj, form, change):
        """Guarda el parque y sincroniza su hospedaje obligatorio de camping."""
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
    """Configuracion administrativa de hospedajes por parque."""

    list_display = ("parque", "tipo_hospedaje", "cantidad_unidades", "capacidad_unidad", "precio_por_unidad")
    list_filter = ("tipo_hospedaje", "parque")
    search_fields = ("parque__nombre",)
