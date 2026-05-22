from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from parques.mapa_adapters import OpenStreetMapAdapter
from parques.mapa_service import MapaService
from parques.models import Hospedaje, Parque, Servicio


class OpenStreetMapAdapterTests(TestCase):
    def test_convierte_parque_a_marcador_para_leaflet(self):
        servicio = Servicio.objects.create(nombre="Sendero nocturno")
        parque = Parque.objects.create(
            nombre="Bosque Claro",
            estado=Parque.Estado.TLAXCALA,
            direccion="Camino al bosque 10",
            latitud=Decimal("19.321000"),
            longitud=Decimal("-98.123000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 30),
            descripcion="Avistamiento guiado.",
        )
        parque.servicios.add(servicio)
        Hospedaje.objects.create(
            parque=parque,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CAMPING,
            cantidad_unidades=4,
            capacidad_unidad=2,
            precio_por_unidad=Decimal("380.00"),
        )

        marcador = OpenStreetMapAdapter().convertir_parque_a_marcador(parque)

        self.assertEqual(marcador["idParque"], parque.id)
        self.assertEqual(marcador["nombre"], "Bosque Claro")
        self.assertEqual(marcador["latitud"], 19.321)
        self.assertEqual(marcador["longitud"], -98.123)
        self.assertEqual(marcador["horario"], "18:00 - 23:30")
        self.assertEqual(marcador["servicios"], ["Sendero nocturno"])
        self.assertEqual(marcador["serviciosValores"], ["sendero-nocturno"])
        self.assertEqual(marcador["hospedajes"], ["Camping"])
        self.assertEqual(marcador["hospedajesValores"], ["camping"])
        self.assertEqual(marcador["estadoValor"], "tlaxcala")
        self.assertEqual(marcador["url"], f"/inicio/parques/{parque.id}/")


class MapaServiceTests(TestCase):
    def test_obtener_marcadores_usa_adapter_inyectado(self):
        Parque.objects.create(
            nombre="Parque de Prueba",
            estado=Parque.Estado.PUEBLA,
            direccion="Direccion de prueba",
            latitud=Decimal("19.100000"),
            longitud=Decimal("-98.200000"),
            horario_apertura=time(19, 0),
            horario_cierre=time(22, 0),
        )

        class AdapterFake:
            def generar_marcadores(self, parques):
                return [{"provider": "fake", "total": len(list(parques))}]

        marcadores = MapaService(AdapterFake()).obtener_marcadores()

        self.assertEqual(marcadores, [{"provider": "fake", "total": 1}])


class InicioMapaRouteTests(TestCase):
    def test_muestra_mapa_con_marcadores(self):
        servicio = Servicio.objects.create(nombre="Sendero nocturno")
        parque = Parque.objects.create(
            nombre="Bosque Mapa",
            estado=Parque.Estado.TLAXCALA,
            direccion="Camino del mapa 12",
            latitud=Decimal("19.321000"),
            longitud=Decimal("-98.123000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 0),
        )
        parque.servicios.add(servicio)

        response = self.client.get(reverse("mapa_parques"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mapa_parques.html")
        self.assertContains(response, 'id="parks-map"')
        self.assertContains(response, "Bosque Mapa")
        self.assertContains(response, "data-map-filter")
        self.assertContains(response, 'data-filter-value="tlaxcala"')
        self.assertContains(response, 'data-filter-value="camping"')
        self.assertContains(response, 'data-filter-value="sendero-nocturno"')
        self.assertContains(response, 'data-map-active-filter-panel')


class InicioHospedajeMinimumsTests(TestCase):
    def test_envia_minimos_de_hospedaje_por_estado_a_la_pagina_de_inicio(self):
        parque_caro = Parque.objects.create(
            nombre="Bosque Caro",
            estado=Parque.Estado.TLAXCALA,
            direccion="Camino caro 1",
            latitud=Decimal("19.111000"),
            longitud=Decimal("-98.111000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 0),
        )
        parque_barato = Parque.objects.create(
            nombre="Bosque Barato",
            estado=Parque.Estado.TLAXCALA,
            direccion="Camino barato 2",
            latitud=Decimal("19.112000"),
            longitud=Decimal("-98.112000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 0),
        )
        Hospedaje.objects.create(
            parque=parque_caro,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CABANA,
            cantidad_unidades=8,
            capacidad_unidad=5,
            precio_por_unidad=Decimal("1800.00"),
        )
        Hospedaje.objects.create(
            parque=parque_barato,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CABANA,
            cantidad_unidades=3,
            capacidad_unidad=2,
            precio_por_unidad=Decimal("1200.00"),
        )

        response = self.client.get(reverse("inicio"))

        minimos = response.context["minimos_hospedaje"]["tlaxcala"]["cabana"]
        self.assertEqual(minimos["precio"], "$1,200 MXN")
        self.assertEqual(minimos["capacidad"], 2)
        self.assertEqual(minimos["unidades"], 3)
        self.assertContains(response, 'id="lodging-minimums-data"')
        self.assertContains(response, 'data-home-map-state-filter="todos"')
        self.assertContains(response, 'data-home-map-state-filter="tlaxcala"')
        self.assertContains(response, 'data-home-map-state-filter="puebla"')
        self.assertContains(response, 'data-home-map-state-filter="edomex"')
        self.assertContains(response, 'data-lodging-state-filter="tlaxcala"')


class ListadoParquesFilterTests(TestCase):
    def test_renderiza_filtros_y_datos_para_filtrado_combinado(self):
        servicio = Servicio.objects.create(nombre="Sendero nocturno")
        parque = Parque.objects.create(
            nombre="Bosque Filtro",
            estado=Parque.Estado.TLAXCALA,
            direccion="Camino filtro 8",
            latitud=Decimal("19.451000"),
            longitud=Decimal("-98.331000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 0),
        )
        parque.servicios.add(servicio)
        Hospedaje.objects.create(
            parque=parque,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CABANA,
            cantidad_unidades=2,
            capacidad_unidad=4,
            precio_por_unidad=Decimal("1200.00"),
        )

        response = self.client.get(reverse("listado_parques"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-filter-value="tlaxcala"')
        self.assertContains(response, 'data-filter-value="cabana"')
        self.assertContains(response, 'data-filter-value="camping"')
        self.assertContains(response, 'data-filter-value="sendero-nocturno"')
        self.assertContains(response, 'data-estado="tlaxcala"')
        self.assertContains(response, 'data-hospedajes="cabana"')
        self.assertContains(response, 'data-servicios="sendero-nocturno"')
        self.assertContains(response, "Hospedaje")
        self.assertContains(response, "<span>Cabaña</span>", html=True)
        self.assertContains(response, "Cabaña: 2 unidades quedan disponibles")
        self.assertContains(response, "data-mini-map")
        self.assertContains(response, "https://www.google.com/maps/search/?api=1&query=19.451000,-98.331000")
        self.assertNotContains(response, "<dt>Coordenadas</dt>", html=True)
        self.assertContains(response, "Vista rapida")
        self.assertContains(response, "Ver parque")
        self.assertContains(response, f'href="{reverse("detalle_parque", args=[parque.id])}"')


class DetalleParqueTests(TestCase):
    def test_muestra_hospedajes_como_etiquetas_en_seccion_separada(self):
        servicio = Servicio.objects.create(nombre="Estacionamiento")
        parque = Parque.objects.create(
            nombre="Bosque Detalle",
            estado=Parque.Estado.PUEBLA,
            direccion="Camino detalle 4",
            latitud=Decimal("19.551000"),
            longitud=Decimal("-98.431000"),
            horario_apertura=time(18, 0),
            horario_cierre=time(23, 0),
        )
        parque.servicios.add(servicio)
        Hospedaje.objects.create(
            parque=parque,
            tipo_hospedaje=Hospedaje.TipoHospedaje.CAMPING,
            cantidad_unidades=6,
            capacidad_unidad=2,
            precio_por_unidad=Decimal("420.00"),
        )

        response = self.client.get(reverse("detalle_parque", args=[parque.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servicios")
        self.assertContains(response, "Hospedaje")
        self.assertContains(response, "<span>Estacionamiento</span>", html=True)
        self.assertContains(response, "<span>Camping</span>", html=True)
        self.assertContains(response, "Camping: 6 espacios quedan disponibles")
        self.assertContains(response, "data-mini-map")
        self.assertContains(response, "https://www.google.com/maps/search/?api=1&query=19.551000,-98.431000")
        self.assertNotContains(response, "<dt>Coordenadas</dt>", html=True)
