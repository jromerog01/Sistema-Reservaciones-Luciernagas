from django.contrib import admin
from django import forms

from parques.models import Parque, Servicio, Hospedaje
from usuarios.models import Usuario

def get_selected_values(value):
    if not value:
        return []

    return [selected_value for selected_value in value.split(",") if selected_value]


def build_multiselect_choices(changelist, parameter_name, selected_values, options):
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
    title = "estado"
    parameter_name = "estado"

    def lookups(self, request, model_admin):
        return Parque.Estado.choices

    def queryset(self, request, queryset):
        estados = self._get_estados()

        if estados:
            return queryset.filter(estado__in=estados)

        return queryset

    def choices(self, changelist):
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_estados(),
            Parque.Estado.choices,
        )

    def _get_estados(self):
        estados_validos = [estado[0] for estado in Parque.Estado.choices]

        return [
            estado
            for estado in get_selected_values(self.value())
            if estado in estados_validos
        ]


class TipoHospedajeParqueFilter(admin.SimpleListFilter):
    title = "tipo de hospedaje"
    parameter_name = "tipo_hospedaje"

    def lookups(self, request, model_admin):
        return (
            (Hospedaje.TipoHospedaje.CABANA, "Cabañas"),
            (Hospedaje.TipoHospedaje.CAMPING, "Camping"),
        )

    def queryset(self, request, queryset):
        tipos_hospedaje = self._get_tipos_hospedaje()

        for tipo_hospedaje in tipos_hospedaje:
            queryset = queryset.filter(hospedajes__tipo_hospedaje=tipo_hospedaje)

        return queryset.distinct()

    def choices(self, changelist):
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_tipos_hospedaje(),
            self.lookups(None, None),
        )

    def _get_tipos_hospedaje(self):
        tipos_validos = [tipo[0] for tipo in Hospedaje.TipoHospedaje.choices]

        return [
            tipo_hospedaje
            for tipo_hospedaje in get_selected_values(self.value())
            if tipo_hospedaje in tipos_validos
        ]


class ServiciosParqueFilter(admin.SimpleListFilter):
    title = "servicios"
    parameter_name = "servicios"

    def lookups(self, request, model_admin):
        return Servicio.objects.values_list("id", "nombre")

    def queryset(self, request, queryset):
        servicios_ids = self._get_servicios_ids()

        for servicio_id in servicios_ids:
            queryset = queryset.filter(servicios__id=servicio_id)

        return queryset.distinct()

    def choices(self, changelist):
        return build_multiselect_choices(
            changelist,
            self.parameter_name,
            self._get_servicios_ids(),
            Servicio.objects.order_by("nombre").values_list("id", "nombre"),
        )

    def _get_servicios_ids(self):
        return [
            servicio_id
            for servicio_id in get_selected_values(self.value())
            if servicio_id.isdigit()
        ]


class ParqueAdminForm(forms.ModelForm):
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
    list_display = ("nombre",)
    # list_editable = ("nombre",)
    search_fields = ("nombre",)
    list_per_page = 20
    # readonly_fields = ("id",)
    # ordering = ("id",)



@admin.register(Parque)
class ParqueAdmin(admin.ModelAdmin):
    form = ParqueAdminForm
    list_display = ("nombre", "estado", "direccion", "latitud", "longitud", "horario_apertura", "horario_cierre", "ver_servicios")
    list_filter = (EstadoParqueFilter, TipoHospedajeParqueFilter, ServiciosParqueFilter)
    search_fields = ("nombre", "direccion", "servicios__nombre")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "servicios":
            kwargs["widget"] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def ver_servicios(self, obj):
        return ", ".join(servicio.nombre for servicio in obj.servicios.all())

    ver_servicios.short_description = "Servicios"

    def save_model(self, request, obj, form, change):
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
    list_display = ("parque", "tipo_hospedaje", "cantidad_unidades", "capacidad_unidad", "precio_por_unidad")
    list_filter = ("tipo_hospedaje", "parque")
    search_fields = ("parque__nombre",)


# Permitir que edite usuarios:

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista de registros
    list_display = ('username',
            'first_name',
            'last_name',
            'email',
            'rol',
            'is_staff')
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username", "is_staff")
    list_filter = ("is_staff",)
    fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'rol',
        'is_staff',
    )
    readonly_fields = ("email", "is_staff", "rol")
    list_per_page = 20
    def has_add_permission(self, request):
        return False