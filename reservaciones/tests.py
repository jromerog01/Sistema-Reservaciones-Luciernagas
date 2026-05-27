"""
Tests del módulo de reservaciones.

Calendario junio 2026 (referencia):
  Lun 1  Mar 2  Mie 3  Jue 4  Vie 5  Sab 6  Dom 7
  Lun 8  Mar 9  ...

Fechas base elegidas:
  JUE (Jun 4) → SAB (Jun 6) : 2 noches (jue+vie), sin martes, en temporada ✓
  LUN (Jun 1) → MIE (Jun 3) : 2 noches (lun+mar), CONTIENE martes ✗
  DOM (Jun 7) → MAR_JUN9 (Jun 9) : 2 noches (dom+lun), checkout martes — válido ✓
"""

import math
from datetime import date, time, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse

from parques.models import Hospedaje, Parque
from reservaciones.forms import (
    ReservacionForm,
    calcular_precio_total,
    calcular_unidades_necesarias,
    fechas_en_temporada,
    rango_incluye_martes,
    unidades_disponibles,
)
from reservaciones.models import Reservacion
from reservaciones.utils.template_method import ReservacionHospedajeTemplate
from usuarios.models import Usuario


# ── Constantes de fecha ──────────────────────────────────────────────────────

LUN      = date(2026, 6, 1)
MAR      = date(2026, 6, 2)
MIE      = date(2026, 6, 3)
JUE      = date(2026, 6, 4)
VIE      = date(2026, 6, 5)
SAB      = date(2026, 6, 6)
DOM      = date(2026, 6, 7)
MAR_JUN9 = date(2026, 6, 9)   # martes, pero como checkout (noches dom+lun) ✓

AGO_30   = date(2026, 8, 30)
AGO_31   = date(2026, 8, 31)
SEP_1    = date(2026, 9, 1)   # checkout válido: última noche = 31-ago ∈ agosto
SEP_2    = date(2026, 9, 2)   # checkout inválido: última noche = 1-sep ∉ temporada

SEP_10   = date(2026, 9, 10)
SEP_14   = date(2026, 9, 14)

MAR_AGO  = date(2026, 8, 4)   # primer martes de agosto


# ── Helpers de fixtures ──────────────────────────────────────────────────────

def crear_parque(nombre="Parque Test", lat="19.300000", lng="-98.100000"):
    return Parque.objects.create(
        nombre=nombre,
        estado=Parque.Estado.TLAXCALA,
        direccion="Calle Prueba 1",
        latitud=Decimal(lat),
        longitud=Decimal(lng),
        horario_apertura=time(18, 0),
        horario_cierre=time(23, 0),
    )


def crear_hospedaje(parque, tipo=Hospedaje.TipoHospedaje.CABANA,
                    unidades=5, capacidad=4, precio="800.00"):
    return Hospedaje.objects.create(
        parque=parque,
        tipo_hospedaje=tipo,
        cantidad_unidades=unidades,
        capacidad_unidad=capacidad,
        precio_por_unidad=Decimal(precio),
    )


def crear_cliente(username="cliente1", email="cliente1@test.com"):
    return Usuario.objects.create_user(
        username=username, email=email,
        password="pass1234", rol=Usuario.Rol.CLIENTE,
    )


def crear_admin(username="admin1", email="admin1@test.com"):
    return Usuario.objects.create_user(
        username=username, email=email,
        password="pass1234", rol=Usuario.Rol.ADMINISTRADOR,
    )


def reservacion_directa(hospedaje, usuario,
                        fecha_inicio=JUE, fecha_fin=SAB,
                        unidades=1, huespedes=2, precio="1600.00"):
    """Crea una Reservacion en BD directamente, sin pasar por el form."""
    return Reservacion.objects.create(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        num_huespedes=huespedes,
        unidades_reservadas=unidades,
        precio_total=Decimal(precio),
        hospedaje=hospedaje,
        usuario=usuario,
    )


# ============================================================================
# 1. Calcular duración de estancia
# ============================================================================

class CalcularDuracionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        cliente = crear_cliente()
        self.reservacion = reservacion_directa(hospedaje, cliente,
                                               fecha_inicio=JUE, fecha_fin=SAB)

    def test_dos_noches(self):
        self.assertEqual(self.reservacion.calcular_duracion(), 2)

    def test_una_noche(self):
        self.reservacion.fecha_inicio = JUE
        self.reservacion.fecha_fin    = VIE
        self.assertEqual(self.reservacion.calcular_duracion(), 1)

    def test_siete_noches(self):
        self.reservacion.fecha_inicio = JUE
        self.reservacion.fecha_fin    = JUE + timedelta(days=7)
        self.assertEqual(self.reservacion.calcular_duracion(), 7)


# ============================================================================
# 2. Calcular unidades necesarias
# ============================================================================

class CalcularUnidadesNecesariasTests(TestCase):

    def test_huespedes_exactos_para_una_unidad(self):
        self.assertEqual(calcular_unidades_necesarias(4, 4), 1)

    def test_redondeo_hacia_arriba(self):
        self.assertEqual(calcular_unidades_necesarias(5, 4), 2)

    def test_un_huesped_siempre_necesita_una_unidad(self):
        self.assertEqual(calcular_unidades_necesarias(1, 10), 1)

    def test_capacidad_exacta_sin_fraccion(self):
        self.assertEqual(calcular_unidades_necesarias(8, 4), 2)

    def test_un_huesped_extra_sube_de_unidad(self):
        self.assertEqual(calcular_unidades_necesarias(9, 4), 3)

    def test_capacidad_cero_lanza_excepcion(self):
        with self.assertRaises(ValueError):
            calcular_unidades_necesarias(3, 0)


# ============================================================================
# 3. Calcular precio total
# ============================================================================

class CalcularPrecioTotalTests(TestCase):

    def test_precio_base(self):
        # 2 unidades × $800 × 3 noches = $4 800
        self.assertEqual(
            calcular_precio_total(2, Decimal("800.00"), 3),
            Decimal("4800.00"),
        )

    def test_una_unidad_una_noche(self):
        self.assertEqual(
            calcular_precio_total(1, Decimal("500.00"), 1),
            Decimal("500.00"),
        )

    def test_precio_con_decimales(self):
        self.assertEqual(
            calcular_precio_total(3, Decimal("666.67"), 2),
            Decimal("4000.02"),
        )


# ============================================================================
# 4. Rechazar reservaciones fuera de junio-agosto
# ============================================================================

class FechasEnTemporadaTests(TestCase):

    def test_junio_valido(self):
        self.assertTrue(fechas_en_temporada(JUE, SAB))

    def test_julio_valido(self):
        self.assertTrue(fechas_en_temporada(date(2026, 7, 6), date(2026, 7, 10)))

    def test_agosto_valido(self):
        self.assertTrue(fechas_en_temporada(date(2026, 8, 3), date(2026, 8, 10)))

    def test_checkout_1sep_ultima_noche_31ago_valido(self):
        self.assertTrue(fechas_en_temporada(AGO_30, SEP_1))

    def test_checkout_2sep_ultima_noche_1sep_invalido(self):
        self.assertFalse(fechas_en_temporada(AGO_30, SEP_2))

    def test_septiembre_invalido(self):
        self.assertFalse(fechas_en_temporada(SEP_10, SEP_14))

    def test_cruce_agosto_septiembre_invalido(self):
        self.assertFalse(fechas_en_temporada(date(2026, 8, 27), date(2026, 9, 5)))

    def test_mayo_invalido(self):
        self.assertFalse(fechas_en_temporada(date(2026, 5, 10), date(2026, 5, 15)))


# ============================================================================
# 5. Rechazar reservaciones que incluyan martes
# ============================================================================

class RangoIncluyeMartesTests(TestCase):

    def test_noche_de_martes_detectada(self):
        # MAR→MIE: única noche = martes
        self.assertTrue(rango_incluye_martes(MAR, MIE))

    def test_lunes_a_miercoles_incluye_martes(self):
        self.assertTrue(rango_incluye_martes(LUN, MIE))

    def test_jueves_a_sabado_sin_martes(self):
        self.assertFalse(rango_incluye_martes(JUE, SAB))

    def test_miercoles_a_viernes_sin_martes(self):
        self.assertFalse(rango_incluye_martes(MIE, VIE))

    def test_solo_noche_de_lunes_sin_martes(self):
        # LUN→MAR: única noche = lunes
        self.assertFalse(rango_incluye_martes(LUN, MAR))

    def test_checkout_martes_noches_sin_martes(self):
        # DOM(7)→MAR(9): noches = dom+lun, checkout martes no cuenta
        self.assertFalse(rango_incluye_martes(DOM, MAR_JUN9))

    def test_martes_de_agosto_detectado(self):
        self.assertTrue(rango_incluye_martes(MAR_AGO, MAR_AGO + timedelta(days=1)))

    def test_semana_larga_con_varios_martes(self):
        self.assertTrue(rango_incluye_martes(LUN, LUN + timedelta(days=15)))


# ============================================================================
# 6. Validar disponibilidad y evitar sobre-reservaciones
# ============================================================================

class UnidadesDisponiblesTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque, unidades=5)
        self.cliente = crear_cliente()

    def test_sin_reservaciones_todas_disponibles(self):
        self.assertEqual(unidades_disponibles(self.hospedaje, JUE, SAB), 5)

    def test_descuenta_reservaciones_activas_solapadas(self):
        reservacion_directa(self.hospedaje, self.cliente, unidades=2)
        self.assertEqual(unidades_disponibles(self.hospedaje, JUE, SAB), 3)

    def test_reservaciones_canceladas_no_cuentan(self):
        r = reservacion_directa(self.hospedaje, self.cliente, unidades=3)
        r.estado = Reservacion.EstadoReservacion.CANCELADA
        r.save()
        self.assertEqual(unidades_disponibles(self.hospedaje, JUE, SAB), 5)

    def test_reservacion_adyacente_no_solapa(self):
        # JUE→SAB ocupado; consulta SAB→DOM no solapa
        reservacion_directa(self.hospedaje, self.cliente,
                            fecha_inicio=JUE, fecha_fin=SAB, unidades=4)
        self.assertEqual(unidades_disponibles(self.hospedaje, SAB, DOM), 5)

    def test_excluir_propia_reservacion_en_edicion(self):
        r = reservacion_directa(self.hospedaje, self.cliente, unidades=3)
        self.assertEqual(
            unidades_disponibles(self.hospedaje, JUE, SAB, excluir_id=r.id), 5
        )

    def test_disponibilidad_cero_cuando_todo_ocupado(self):
        reservacion_directa(self.hospedaje, self.cliente, unidades=5)
        self.assertEqual(unidades_disponibles(self.hospedaje, JUE, SAB), 0)

    def test_multiples_reservaciones_parciales_se_suman(self):
        cliente2 = crear_cliente(username="cli2", email="cli2@test.com")
        reservacion_directa(self.hospedaje, self.cliente,  unidades=2)
        reservacion_directa(self.hospedaje, cliente2,      unidades=2)
        self.assertEqual(unidades_disponibles(self.hospedaje, JUE, SAB), 1)


# ============================================================================
# 7. Form — validaciones integradas
# ============================================================================

class ReservacionFormTests(TestCase):
    """
    Datos por defecto: JUE→SAB (2 noches), 2 huéspedes, 1 unidad.
    Hospedaje: 5 unidades, capacidad 4, precio $800.
    """

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque, unidades=5, capacidad=4, precio="800.00")

    def _form(self, **kwargs):
        datos = {
            "fecha_inicio":        JUE.isoformat(),
            "fecha_fin":           SAB.isoformat(),
            "num_huespedes":       2,
            "unidades_reservadas": 1,
        }
        datos.update(kwargs)
        return ReservacionForm(datos, hospedaje=self.hospedaje)

    # ── Caso base válido ─────────────────────────────────────────────────────

    def test_form_valido_con_datos_correctos(self):
        self.assertTrue(self._form().is_valid())

    def test_fecha_fin_igual_a_inicio_invalida(self):
        self.assertFalse(
            self._form(fecha_inicio=JUE.isoformat(), fecha_fin=JUE.isoformat()).is_valid()
        )

    def test_fecha_inicio_en_pasado_invalida(self):
        ayer = date.today() - timedelta(days=1)
        self.assertFalse(
            self._form(
                fecha_inicio=ayer.isoformat(),
                fecha_fin=(ayer + timedelta(days=2)).isoformat(),
            ).is_valid()
        )

    # ── Temporada ────────────────────────────────────────────────────────────

    def test_rechaza_fuera_de_temporada(self):
        form = self._form(fecha_inicio=SEP_10.isoformat(), fecha_fin=SEP_14.isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn("junio a agosto", " ".join(form.errors.get("fecha_inicio", [])))

    def test_rechaza_cruce_agosto_septiembre(self):
        self.assertFalse(
            self._form(
                fecha_inicio=date(2026, 8, 27).isoformat(),
                fecha_fin=SEP_2.isoformat(),
            ).is_valid()
        )

    def test_acepta_checkout_1_septiembre(self):
        # Última noche = 31-ago ∈ temporada ✓
        form = self._form(fecha_inicio=AGO_30.isoformat(), fecha_fin=SEP_1.isoformat())
        self.assertTrue(form.is_valid(), form.errors)

    # ── Martes ───────────────────────────────────────────────────────────────

    def test_rechaza_estancia_con_martes(self):
        # LUN→MIE: noches lun+mar → contiene martes
        form = self._form(fecha_inicio=LUN.isoformat(), fecha_fin=MIE.isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn("martes", " ".join(form.errors.get("fecha_inicio", [])))

    def test_rechaza_noche_unica_de_martes(self):
        self.assertFalse(
            self._form(fecha_inicio=MAR.isoformat(), fecha_fin=MIE.isoformat()).is_valid()
        )

    def test_acepta_checkout_en_martes_sin_noche_de_martes(self):
        # DOM(7)→MAR(9): noches dom+lun, sin martes ✓
        form = self._form(fecha_inicio=DOM.isoformat(), fecha_fin=MAR_JUN9.isoformat())
        self.assertTrue(form.is_valid(), form.errors)

    # ── Unidades necesarias ──────────────────────────────────────────────────

    def test_rechaza_unidades_insuficientes(self):
        # 5 huéspedes, capacidad 4 → mín 2 unidades; se pide 1
        form = self._form(num_huespedes=5, unidades_reservadas=1)
        self.assertFalse(form.is_valid())
        self.assertIn("2 unidad", " ".join(form.errors.get("unidades_reservadas", [])))

    def test_acepta_unidades_exactas(self):
        # 4 huéspedes, capacidad 4 → 1 unidad exacta ✓
        self.assertTrue(self._form(num_huespedes=4, unidades_reservadas=1).is_valid())

    def test_acepta_unidades_superiores(self):
        self.assertTrue(self._form(num_huespedes=2, unidades_reservadas=2).is_valid())

    # ── Disponibilidad / sobre-reservación ──────────────────────────────────

    def test_rechaza_cuando_no_hay_disponibilidad(self):
        cliente = crear_cliente()
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        form = self._form(unidades_reservadas=1)
        self.assertFalse(form.is_valid())
        self.assertIn("0 unidad", " ".join(form.errors.get("unidades_reservadas", [])))

    def test_acepta_con_unidades_suficientes(self):
        cliente = crear_cliente()
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=3,
            precio_total=Decimal("4800.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        self.assertTrue(self._form(unidades_reservadas=2).is_valid())

    def test_canceladas_no_afectan_disponibilidad(self):
        cliente = crear_cliente()
        r = Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        r.estado = Reservacion.EstadoReservacion.CANCELADA
        r.save()
        self.assertTrue(self._form(unidades_reservadas=2).is_valid())

    # ── calcular_precio ──────────────────────────────────────────────────────

    def test_calcular_precio_correcto(self):
        # 2 unidades × $800 × 2 noches = $3 200
        form = self._form(unidades_reservadas=2)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.calcular_precio(), Decimal("3200.00"))

    def test_calcular_precio_none_si_invalido(self):
        form = self._form(fecha_inicio=SEP_10.isoformat(), fecha_fin=SEP_14.isoformat())
        self.assertIsNone(form.calcular_precio())


# ============================================================================
# 8. Vista: crear reservación
# ============================================================================

class CrearReservacionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque, unidades=5, capacidad=4, precio="800.00")
        self.cliente   = crear_cliente()
        self.url       = reverse("crear_reservacion", args=[self.hospedaje.id])

    def _post(self, **kwargs):
        datos = {
            "fecha_inicio":        JUE.isoformat(),
            "fecha_fin":           SAB.isoformat(),
            "num_huespedes":       2,
            "unidades_reservadas": 1,
        }
        datos.update(kwargs)
        return self.client.post(self.url, datos)

    def test_redirige_a_login_si_no_autenticado(self):
        resp = self.client.get(self.url)
        self.assertIn(reverse("usuarios:login"), resp["Location"])
        self.assertIn("next=", resp["Location"])

    def test_crea_reservacion_valida_y_redirige(self):
        self.client.force_login(self.cliente)
        resp = self._post()
        self.assertEqual(Reservacion.objects.count(), 1)
        r = Reservacion.objects.first()
        self.assertRedirects(resp, reverse("detalle_reservacion", args=[r.id]))

    def test_precio_calculado_correctamente(self):
        # 1 unidad × $800 × 2 noches = $1 600
        self.client.force_login(self.cliente)
        self._post()
        self.assertEqual(Reservacion.objects.first().precio_total, Decimal("1600.00"))

    def test_reservacion_queda_asociada_al_usuario(self):
        self.client.force_login(self.cliente)
        self._post()
        self.assertEqual(Reservacion.objects.first().usuario, self.cliente)

    def test_rechaza_fuera_de_temporada(self):
        self.client.force_login(self.cliente)
        resp = self._post(fecha_inicio=SEP_10.isoformat(), fecha_fin=SEP_14.isoformat())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_rechaza_con_martes(self):
        self.client.force_login(self.cliente)
        resp = self._post(fecha_inicio=LUN.isoformat(), fecha_fin=MIE.isoformat())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_rechaza_sobre_reservacion(self):
        self.client.force_login(self.cliente)
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=self.cliente,
        )
        resp = self._post(unidades_reservadas=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 1)   # no se creó una más

    def test_rechaza_unidades_insuficientes(self):
        self.client.force_login(self.cliente)
        resp = self._post(num_huespedes=5, unidades_reservadas=1)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_rechaza_si_el_cupo_cambia_antes_de_guardar(self):
        self.client.force_login(self.cliente)
        factory = RequestFactory()
        form = ReservacionForm(
            {
                "fecha_inicio": JUE.isoformat(),
                "fecha_fin": SAB.isoformat(),
                "num_huespedes": 2,
                "unidades_reservadas": 1,
            },
            hospedaje=self.hospedaje,
        )
        self.assertTrue(form.is_valid(), form.errors)

        reservacion_directa(
            self.hospedaje,
            crear_cliente(username="otro-cupo", email="otro-cupo@test.com"),
            unidades=5,
            huespedes=4,
            precio="8000.00",
        )

        request = factory.post(self.url)
        request.user = self.cliente
        processor = ReservacionHospedajeTemplate(request, self.hospedaje, form)

        reservacion = processor.procesar_reservacion()

        self.assertIsNone(reservacion)
        self.assertIn("Solo quedan 0 unidad", " ".join(form.errors.get("unidades_reservadas", [])))
        self.assertEqual(Reservacion.objects.count(), 1)


# ============================================================================
# 9. Vista: cancelar reservación
# ============================================================================

class CancelarReservacionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        self.cliente     = crear_cliente()
        self.otro        = crear_cliente(username="otro",  email="otro@test.com")
        self.admin       = crear_admin()
        self.reservacion = reservacion_directa(hospedaje, self.cliente)
        self.url         = reverse("cancelar_reservacion", args=[self.reservacion.id])

    def test_propietario_puede_cancelar(self):
        self.client.force_login(self.cliente)
        self.client.post(self.url)
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_admin_puede_cancelar(self):
        self.client.force_login(self.admin)
        self.client.post(self.url)
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_otro_cliente_recibe_403(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_no_cancela_reservacion_ya_cancelada(self):
        self.reservacion.estado = Reservacion.EstadoReservacion.CANCELADA
        self.reservacion.save()
        self.client.force_login(self.cliente)
        resp = self.client.post(self.url)
        self.assertContains(resp, "Solo se pueden cancelar reservaciones activas")

    def test_cancelar_redirige_a_mis_reservaciones(self):
        self.client.force_login(self.cliente)
        resp = self.client.post(self.url)
        self.assertRedirects(resp, reverse("mis_reservaciones"))


# ============================================================================
# 10. Vista: consultar reservaciones del cliente (mis_reservaciones)
# ============================================================================

class MisReservacionesTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque)
        self.cliente   = crear_cliente()
        self.otro      = crear_cliente(username="otro2", email="otro2@test.com")
        self.url       = reverse("mis_reservaciones")

    def test_muestra_solo_reservaciones_propias(self):
        propia = reservacion_directa(self.hospedaje, self.cliente)
        reservacion_directa(self.hospedaje, self.otro)          # de otro usuario
        self.client.force_login(self.cliente)
        resp = self.client.get(self.url)
        lista = list(resp.context["reservaciones"])
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0].id, propia.id)

    def test_muestra_duracion_correcta(self):
        reservacion_directa(self.hospedaje, self.cliente,
                            fecha_inicio=JUE, fecha_fin=SAB)   # 2 noches
        self.client.force_login(self.cliente)
        resp = self.client.get(self.url)
        self.assertContains(resp, "2 noche(s)")

    def test_muestra_mensaje_sin_reservaciones(self):
        self.client.force_login(self.cliente)
        resp = self.client.get(self.url)
        self.assertContains(resp, "No tienes reservaciones registradas")

    def test_requiere_autenticacion(self):
        resp = self.client.get(self.url)
        self.assertIn(reverse("usuarios:login"), resp["Location"])


# ============================================================================
# 11. Vista: consultar todas las reservaciones como administrador
# ============================================================================

class TodasLasReservacionesTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque)
        self.cliente   = crear_cliente()
        self.admin     = crear_admin()
        self.url       = reverse("todas_las_reservaciones")

    def test_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonimo_redirige_a_login(self):
        resp = self.client.get(self.url)
        self.assertIn(reverse("usuarios:login"), resp["Location"])

    def test_admin_ve_todas_las_reservaciones(self):
        reservacion_directa(self.hospedaje, self.cliente)
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["reservaciones"].count(), 1)

    def test_admin_ve_reservaciones_de_distintos_clientes(self):
        otro = crear_cliente(username="otro3", email="otro3@test.com")
        reservacion_directa(self.hospedaje, self.cliente)
        reservacion_directa(self.hospedaje, otro)
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["reservaciones"].count(), 2)

    def test_admin_ve_nombre_del_cliente_en_respuesta(self):
        reservacion_directa(self.hospedaje, self.cliente)
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertContains(resp, str(self.cliente))


# ============================================================================
# 12. Vista: detalle de reservación
# ============================================================================

class DetalleReservacionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        self.cliente     = crear_cliente()
        self.otro        = crear_cliente(username="otro4", email="otro4@test.com")
        self.admin       = crear_admin()
        self.reservacion = reservacion_directa(hospedaje, self.cliente,
                                               fecha_inicio=JUE, fecha_fin=SAB)
        self.url = reverse("detalle_reservacion", args=[self.reservacion.id])

    def test_propietario_ve_su_reservacion(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_admin_ve_cualquier_reservacion(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_otro_cliente_recibe_403(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_muestra_duracion_en_contexto(self):
        # JUE→SAB = 2 noches
        self.client.force_login(self.cliente)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["duracion"], 2)
        self.assertContains(resp, "2 noche(s)")