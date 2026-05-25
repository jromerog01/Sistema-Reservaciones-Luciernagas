"""
Tests del módulo de reservaciones.

Calendario junio 2026 (referencia):
  Lun 1  Mar 2  Mie 3  Jue 4  Vie 5  Sab 6  Dom 7
  Lun 8  Mar 9  ...

Fechas base elegidas para los tests:
  JUE (Jun 4) → SAB (Jun 6) : noches jue+vie, sin martes, en temporada ✓
  DOM (Jun 7) → MAR_JUN9 (Jun 9) : noches dom+lun, checkout martes ✓

Fuera de temporada (futuras):
  SEP_10 (10-sep) → SEP_14 (14-sep)
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from parques.models import Hospedaje, Parque
from reservaciones.models import Reservacion
from usuarios.models import Usuario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def crear_parque(nombre="Parque Test", lat="19.300000", lng="-98.100000"):
    return Parque.objects.create(
        nombre=nombre, estado=Parque.Estado.TLAXCALA,
        direccion="Calle Prueba 1",
        latitud=Decimal(lat), longitud=Decimal(lng),
        horario_apertura=time(18, 0), horario_cierre=time(23, 0),
    )


def crear_hospedaje(parque, tipo=Hospedaje.TipoHospedaje.CABANA,
                    unidades=5, capacidad=4, precio="800.00"):
    return Hospedaje.objects.create(
        parque=parque, tipo_hospedaje=tipo,
        cantidad_unidades=unidades, capacidad_unidad=capacidad,
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


# ── Fechas en temporada ──────────────────────────────────────────────────────
LUN     = date(2026, 6, 1)   # lunes
MAR     = date(2026, 6, 2)   # martes
MIE     = date(2026, 6, 3)   # miércoles
JUE     = date(2026, 6, 4)   # jueves   ← inicio por defecto en los forms
VIE     = date(2026, 6, 5)   # viernes
SAB     = date(2026, 6, 6)   # sábado   ← fin por defecto en los forms
DOM     = date(2026, 6, 7)   # domingo
MAR_JUN9 = date(2026, 6, 9)  # martes (checkout, las noches son dom+lun)

MAR_AGO = date(2026, 8, 4)   # primer martes de agosto
AGO_30  = date(2026, 8, 30)  # sábado (fin de agosto)
AGO_31  = date(2026, 8, 31)  # domingo — último día de temporada como noche
SEP_1   = date(2026, 9, 1)   # lunes — checkout válido (última noche = ago-31)
SEP_2   = date(2026, 9, 2)   # martes — checkout inválido (noche sep-1 fuera)

# ── Fuera de temporada (fechas futuras para no confundir con validación pasado)
SEP_10  = date(2026, 9, 10)  # jueves
SEP_14  = date(2026, 9, 14)  # lunes


def reservacion_directa(hospedaje, usuario,
                        fecha_inicio=JUE, fecha_fin=SAB,
                        unidades=1, huespedes=2, precio="1600.00"):
    """Crea una Reservacion en BD directamente, sin pasar por el form."""
    return Reservacion.objects.create(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        num_huespedes=huespedes, unidades_reservadas=unidades,
        precio_total=Decimal(precio),
        hospedaje=hospedaje, usuario=usuario,
    )


# ---------------------------------------------------------------------------
# Modelo – calcular_unidades_necesarias
# ---------------------------------------------------------------------------

class CalcularUnidadesNecesariasTests(TestCase):

    def test_huespedes_exactos_para_una_unidad(self):
        self.assertEqual(Reservacion.calcular_unidades_necesarias(4, 4), 1)

    def test_huespedes_que_requieren_redondeo_hacia_arriba(self):
        self.assertEqual(Reservacion.calcular_unidades_necesarias(5, 4), 2)

    def test_un_huesped_siempre_necesita_al_menos_una_unidad(self):
        self.assertEqual(Reservacion.calcular_unidades_necesarias(1, 10), 1)

    def test_capacidad_exacta_sin_fraccion(self):
        self.assertEqual(Reservacion.calcular_unidades_necesarias(8, 4), 2)

    def test_un_huesped_extra_sube_de_unidad(self):
        self.assertEqual(Reservacion.calcular_unidades_necesarias(9, 4), 3)

    def test_capacidad_cero_lanza_excepcion(self):
        with self.assertRaises(ValueError):
            Reservacion.calcular_unidades_necesarias(3, 0)


# ---------------------------------------------------------------------------
# Modelo – calcular_precio_total
# ---------------------------------------------------------------------------

class CalcularPrecioTotalTests(TestCase):

    def test_precio_total_correcto(self):
        # 2 unidades × $800 × 3 noches = $4 800
        self.assertEqual(
            Reservacion.calcular_precio_total(2, Decimal("800.00"), 3),
            Decimal("4800.00"),
        )

    def test_una_unidad_una_noche(self):
        self.assertEqual(
            Reservacion.calcular_precio_total(1, Decimal("500.00"), 1),
            Decimal("500.00"),
        )

    def test_precio_con_decimales(self):
        self.assertEqual(
            Reservacion.calcular_precio_total(3, Decimal("666.67"), 2),
            Decimal("4000.02"),
        )


# ---------------------------------------------------------------------------
# Modelo – fechas_en_temporada
# ---------------------------------------------------------------------------

class FechasEnTemporadaTests(TestCase):

    def test_junio_completo_es_temporada(self):
        self.assertTrue(Reservacion.fechas_en_temporada(JUE, SAB))

    def test_julio_es_temporada(self):
        ini = date(2026, 7, 6)
        fin = date(2026, 7, 10)
        self.assertTrue(Reservacion.fechas_en_temporada(ini, fin))

    def test_agosto_es_temporada(self):
        ini = date(2026, 8, 3)
        fin = date(2026, 8, 10)
        self.assertTrue(Reservacion.fechas_en_temporada(ini, fin))

    def test_checkout_sep1_ultima_noche_ago31_es_valido(self):
        self.assertTrue(Reservacion.fechas_en_temporada(AGO_30, SEP_1))

    def test_checkout_sep2_ultima_noche_sep1_invalido(self):
        self.assertFalse(Reservacion.fechas_en_temporada(AGO_30, SEP_2))

    def test_septiembre_es_fuera_de_temporada(self):
        self.assertFalse(Reservacion.fechas_en_temporada(SEP_10, SEP_14))

    def test_inicio_junio_fin_septiembre_invalido(self):
        self.assertFalse(Reservacion.fechas_en_temporada(JUE, SEP_10))

    def test_cruce_agosto_septiembre_invalido(self):
        ini = date(2026, 8, 27)  # jueves
        fin = date(2026, 9, 5)
        self.assertFalse(Reservacion.fechas_en_temporada(ini, fin))


# ---------------------------------------------------------------------------
# Modelo – rango_incluye_martes
# ---------------------------------------------------------------------------

class RangoIncluyeMartesTests(TestCase):

    def test_martes_solo_es_detectado(self):
        # MAR→MIE: única noche = martes
        self.assertTrue(Reservacion.rango_incluye_martes(MAR, MIE))

    def test_lunes_a_miercoles_incluye_martes(self):
        self.assertTrue(Reservacion.rango_incluye_martes(LUN, MIE))

    def test_miercoles_a_viernes_sin_martes(self):
        # MIE→VIE: noches mié+jue, sin martes
        self.assertFalse(Reservacion.rango_incluye_martes(MIE, VIE))

    def test_jueves_a_sabado_sin_martes(self):
        # JUE→SAB: noches jue+vie, sin martes
        self.assertFalse(Reservacion.rango_incluye_martes(JUE, SAB))

    def test_lunes_solo_sin_martes(self):
        # LUN→MAR: única noche = lunes, sin martes
        self.assertFalse(Reservacion.rango_incluye_martes(LUN, MAR))

    def test_semana_larga_con_dos_martes(self):
        self.assertTrue(Reservacion.rango_incluye_martes(LUN, LUN + timedelta(days=15)))

    def test_martes_agosto_detectado(self):
        self.assertTrue(Reservacion.rango_incluye_martes(MAR_AGO, MAR_AGO + timedelta(days=1)))

    def test_checkout_martes_noches_sin_martes(self):
        # DOM→MAR_JUN9: noches dom(7)+lun(8), checkout martes(9) no cuenta
        self.assertFalse(Reservacion.rango_incluye_martes(DOM, MAR_JUN9))


# ---------------------------------------------------------------------------
# Modelo – unidades_disponibles / sobre-reservaciones
# ---------------------------------------------------------------------------

class UnidadesDisponiblesTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque, unidades=5)
        self.cliente = crear_cliente()

    def test_sin_reservaciones_todas_disponibles(self):
        self.assertEqual(
            Reservacion.unidades_disponibles(self.hospedaje, JUE, SAB), 5
        )

    def test_descuenta_reservaciones_activas_solapadas(self):
        # JUE→SAB ocupa 2 unidades
        reservacion_directa(self.hospedaje, self.cliente,
                            fecha_inicio=JUE, fecha_fin=SAB, unidades=2)
        self.assertEqual(
            Reservacion.unidades_disponibles(self.hospedaje, JUE, SAB), 3
        )

    def test_reservaciones_canceladas_no_cuentan(self):
        r = reservacion_directa(self.hospedaje, self.cliente, unidades=3)
        r.estado = Reservacion.EstadoReservacion.CANCELADA
        r.save()
        self.assertEqual(
            Reservacion.unidades_disponibles(self.hospedaje, JUE, SAB), 5
        )

    def test_reservacion_adyacente_no_solapa(self):
        # JUE→SAB ocupado; consulta SAB→DOM: sin solapamiento
        reservacion_directa(self.hospedaje, self.cliente,
                            fecha_inicio=JUE, fecha_fin=SAB, unidades=4)
        self.assertEqual(
            Reservacion.unidades_disponibles(self.hospedaje, SAB, DOM), 5
        )

    def test_excluir_propia_reservacion_en_edicion(self):
        r = reservacion_directa(self.hospedaje, self.cliente, unidades=3)
        self.assertEqual(
            Reservacion.unidades_disponibles(
                self.hospedaje, JUE, SAB, excluir_id=r.id
            ), 5
        )

    def test_disponibilidad_cero_cuando_todo_ocupado(self):
        reservacion_directa(self.hospedaje, self.cliente,
                            fecha_inicio=JUE, fecha_fin=SAB, unidades=5)
        self.assertEqual(
            Reservacion.unidades_disponibles(self.hospedaje, JUE, SAB), 0
        )


# ---------------------------------------------------------------------------
# Form – validaciones integradas
# ---------------------------------------------------------------------------

class ReservacionFormTests(TestCase):
    """
    Form default: JUE (Jun 4) → SAB (Jun 6)
      - 2 noches (jue + vie), sin martes, en temporada ✓
      - Precio base: 1 unidad × $800 × 2 noches = $1 600
    """

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque, unidades=5, capacidad=4,
                                         precio="800.00")

    def _form(self, **kwargs):
        from reservaciones.forms import ReservacionForm
        datos = {
            "fecha_inicio":        JUE.isoformat(),   # jueves 4-jun
            "fecha_fin":           SAB.isoformat(),   # sábado 6-jun (2 noches)
            "num_huespedes":       2,
            "unidades_reservadas": 1,
        }
        datos.update(kwargs)
        return ReservacionForm(datos, hospedaje=self.hospedaje)

    # ── Validez base ────────────────────────────────────────────────────────

    def test_form_valido_con_datos_correctos(self):
        self.assertTrue(self._form().is_valid())

    def test_fecha_fin_igual_a_inicio_es_invalida(self):
        self.assertFalse(self._form(
            fecha_inicio=JUE.isoformat(), fecha_fin=JUE.isoformat()
        ).is_valid())

    def test_fecha_inicio_en_pasado_es_invalida(self):
        ayer = date.today() - timedelta(days=1)
        form = self._form(
            fecha_inicio=ayer.isoformat(),
            fecha_fin=(ayer + timedelta(days=2)).isoformat(),
        )
        self.assertFalse(form.is_valid())

    # ── Temporada ───────────────────────────────────────────────────────────

    def test_rechaza_fuera_de_temporada(self):
        form = self._form(
            fecha_inicio=SEP_10.isoformat(),
            fecha_fin=SEP_14.isoformat(),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("junio a agosto", " ".join(form.errors.get("fecha_inicio", [])))

    def test_rechaza_estancia_que_cruza_septiembre(self):
        form = self._form(
            fecha_inicio=date(2026, 8, 27).isoformat(),  # jueves
            fecha_fin=SEP_2.isoformat(),
        )
        self.assertFalse(form.is_valid())

    def test_acepta_checkout_el_1_de_septiembre(self):
        # Llega 30-ago (sab), sale 1-sep (lun) → última noche = 31-ago ∈ agosto
        form = self._form(
            fecha_inicio=AGO_30.isoformat(),
            fecha_fin=SEP_1.isoformat(),
        )
        self.assertTrue(form.is_valid(), form.errors)

    # ── Martes ──────────────────────────────────────────────────────────────

    def test_rechaza_estancia_que_incluye_martes(self):
        # LUN→MIE: noches lun+mar → contiene martes
        form = self._form(fecha_inicio=LUN.isoformat(), fecha_fin=MIE.isoformat())
        self.assertFalse(form.is_valid())
        self.assertIn("martes", " ".join(form.errors.get("fecha_inicio", [])))

    def test_rechaza_estancia_de_una_noche_en_martes(self):
        form = self._form(fecha_inicio=MAR.isoformat(), fecha_fin=MIE.isoformat())
        self.assertFalse(form.is_valid())

    def test_acepta_estancia_sin_ningun_martes(self):
        # MIE→VIE: noches mié+jue, sin martes
        form = self._form(fecha_inicio=MIE.isoformat(), fecha_fin=VIE.isoformat())
        self.assertTrue(form.is_valid(), form.errors)

    def test_acepta_checkout_en_martes_sin_noche_de_martes(self):
        # DOM(7-jun)→MAR_JUN9(9-jun): noches dom+lun, checkout martes no cuenta
        form = self._form(
            fecha_inicio=DOM.isoformat(),
            fecha_fin=MAR_JUN9.isoformat(),
        )
        self.assertTrue(form.is_valid(), form.errors)

    # ── Unidades necesarias ─────────────────────────────────────────────────

    def test_rechaza_unidades_insuficientes_para_huespedes(self):
        # 5 huéspedes, capacidad 4 → mín 2 unidades; se pide 1
        form = self._form(num_huespedes=5, unidades_reservadas=1)
        self.assertFalse(form.is_valid())
        self.assertIn("2 unidad", " ".join(form.errors.get("unidades_reservadas", [])))

    def test_acepta_unidades_exactamente_necesarias(self):
        # 4 huéspedes, capacidad 4 → 1 unidad exacta
        form = self._form(num_huespedes=4, unidades_reservadas=1)
        self.assertTrue(form.is_valid(), form.errors)

    def test_acepta_unidades_superiores_a_las_necesarias(self):
        form = self._form(num_huespedes=2, unidades_reservadas=2)
        self.assertTrue(form.is_valid(), form.errors)

    # ── Disponibilidad / sobre-reservaciones ────────────────────────────────

    def test_rechaza_cuando_no_hay_unidades_disponibles(self):
        cliente = crear_cliente()
        # Ocupa las 5 unidades en el mismo periodo JUE→SAB
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        form = self._form(unidades_reservadas=1)
        self.assertFalse(form.is_valid())
        self.assertIn("0 unidad", " ".join(form.errors.get("unidades_reservadas", [])))

    def test_acepta_cuando_hay_unidades_suficientes(self):
        cliente = crear_cliente()
        # Ocupa 3 de 5 en JUE→SAB
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=3,
            precio_total=Decimal("4800.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        form = self._form(unidades_reservadas=2)
        self.assertTrue(form.is_valid(), form.errors)

    def test_reservaciones_canceladas_no_afectan_disponibilidad(self):
        cliente = crear_cliente()
        r = Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=cliente,
        )
        r.estado = Reservacion.EstadoReservacion.CANCELADA
        r.save()
        form = self._form(unidades_reservadas=2)
        self.assertTrue(form.is_valid(), form.errors)

    # ── calcular_precio ──────────────────────────────────────────────────────

    def test_calcular_precio_retorna_monto_correcto(self):
        # 2 unidades × $800 × 2 noches (jue+vie) = $3 200
        form = self._form(unidades_reservadas=2)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.calcular_precio(), Decimal("3200.00"))

    def test_calcular_precio_none_si_form_invalido(self):
        form = self._form(
            fecha_inicio=SEP_10.isoformat(),
            fecha_fin=SEP_14.isoformat(),
        )
        self.assertIsNone(form.calcular_precio())


# ---------------------------------------------------------------------------
# Vista: crear_reservacion (integración)
# ---------------------------------------------------------------------------

class CrearReservacionVistasTests(TestCase):
    """
    Datos por defecto: JUE→SAB, 2 huéspedes, 1 unidad.
    Precio esperado: 1 × $800 × 2 noches = $1 600.
    """

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque, unidades=5, capacidad=4,
                                          precio="800.00")
        self.cliente = crear_cliente()

    def _url(self):
        return reverse("crear_reservacion", args=[self.hospedaje.id])

    def _post(self, **kwargs):
        datos = {
            "fecha_inicio":        JUE.isoformat(),
            "fecha_fin":           SAB.isoformat(),
            "num_huespedes":       2,
            "unidades_reservadas": 1,
        }
        datos.update(kwargs)
        return self.client.post(self._url(), datos)

    def test_redirige_a_login_si_no_autenticado(self):
        self.assertIn("/accounts/login/", self.client.get(self._url())["Location"])

    def test_crea_reservacion_valida_y_redirige(self):
        self.client.force_login(self.cliente)
        response = self._post()
        self.assertEqual(Reservacion.objects.count(), 1)
        r = Reservacion.objects.first()
        self.assertRedirects(response, reverse("detalle_reservacion", args=[r.id]))

    def test_precio_calculado_automaticamente(self):
        # 1 unidad × $800 × 2 noches = $1 600
        self.client.force_login(self.cliente)
        self._post()
        self.assertEqual(Reservacion.objects.first().precio_total, Decimal("1600.00"))

    def test_rechaza_fuera_de_temporada(self):
        self.client.force_login(self.cliente)
        response = self._post(
            fecha_inicio=SEP_10.isoformat(),
            fecha_fin=SEP_14.isoformat(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_rechaza_con_martes(self):
        self.client.force_login(self.cliente)
        # LUN→MIE incluye martes
        response = self._post(fecha_inicio=LUN.isoformat(), fecha_fin=MIE.isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_rechaza_sobre_reservacion(self):
        self.client.force_login(self.cliente)
        # Ocupa las 5 unidades en JUE→SAB
        Reservacion.objects.create(
            fecha_inicio=JUE, fecha_fin=SAB,
            num_huespedes=4, unidades_reservadas=5,
            precio_total=Decimal("8000.00"),
            hospedaje=self.hospedaje, usuario=self.cliente,
        )
        response = self._post(unidades_reservadas=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 1)  # no se creó una más

    def test_rechaza_unidades_insuficientes_para_huespedes(self):
        self.client.force_login(self.cliente)
        response = self._post(num_huespedes=5, unidades_reservadas=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_reservacion_queda_asociada_al_usuario_autenticado(self):
        self.client.force_login(self.cliente)
        self._post()
        self.assertEqual(Reservacion.objects.first().usuario, self.cliente)


# ---------------------------------------------------------------------------
# Vista: cancelar_reservacion
# ---------------------------------------------------------------------------

class CancelarReservacionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        self.cliente = crear_cliente()
        self.otro = crear_cliente(username="otro", email="otro@test.com")
        self.admin = crear_admin()
        self.reservacion = reservacion_directa(hospedaje, self.cliente)

    def _url(self):
        return reverse("cancelar_reservacion", args=[self.reservacion.id])

    def test_propietario_puede_cancelar(self):
        self.client.force_login(self.cliente)
        self.client.post(self._url())
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_admin_puede_cancelar(self):
        self.client.force_login(self.admin)
        self.client.post(self._url())
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_otro_cliente_recibe_403(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.post(self._url()).status_code, 403)

    def test_no_cancela_reservacion_ya_cancelada(self):
        self.reservacion.estado = Reservacion.EstadoReservacion.CANCELADA
        self.reservacion.save()
        self.client.force_login(self.cliente)
        response = self.client.post(self._url())
        self.assertContains(response, "Solo se pueden cancelar reservaciones activas")

    def test_cancelar_redirige_a_mis_reservaciones(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self._url())
        self.assertRedirects(response, reverse("mis_reservaciones"))


# ---------------------------------------------------------------------------
# Vista: mis_reservaciones
# ---------------------------------------------------------------------------

class MisReservacionesTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque)
        self.cliente = crear_cliente()
        self.otro = crear_cliente(username="otro2", email="otro2@test.com")

    def test_muestra_solo_reservaciones_del_cliente(self):
        r_propia = reservacion_directa(self.hospedaje, self.cliente)
        reservacion_directa(self.hospedaje, self.otro)
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("mis_reservaciones"))
        reservaciones = list(response.context["reservaciones"])
        self.assertEqual(len(reservaciones), 1)
        self.assertEqual(reservaciones[0].id, r_propia.id)

    def test_muestra_duracion_calculada(self):
        reservacion_directa(self.hospedaje, self.cliente)  # JUE→SAB = 2 noches
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("mis_reservaciones"))
        self.assertContains(response, "2 noche(s)")

    def test_muestra_mensaje_sin_reservaciones(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse("mis_reservaciones"))
        self.assertContains(response, "No tienes reservaciones registradas")


# ---------------------------------------------------------------------------
# Vista: todas_las_reservaciones
# ---------------------------------------------------------------------------

class TodasLasReservacionesTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque)
        self.cliente = crear_cliente()
        self.admin = crear_admin()

    def test_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(
            self.client.get(reverse("todas_las_reservaciones")).status_code, 403
        )

    def test_admin_ve_todas(self):
        reservacion_directa(self.hospedaje, self.cliente)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("todas_las_reservaciones"))
        self.assertEqual(response.context["reservaciones"].count(), 1)

    def test_admin_ve_nombre_del_cliente(self):
        reservacion_directa(self.hospedaje, self.cliente)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("todas_las_reservaciones"))
        self.assertContains(response, str(self.cliente))


# ---------------------------------------------------------------------------
# Vista: detalle_reservacion
# ---------------------------------------------------------------------------

class DetalleReservacionTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        self.cliente = crear_cliente()
        self.otro = crear_cliente(username="otro3", email="otro3@test.com")
        self.admin = crear_admin()
        self.reservacion = reservacion_directa(hospedaje, self.cliente)

    def _url(self):
        return reverse("detalle_reservacion", args=[self.reservacion.id])

    def test_propietario_ve_su_reservacion(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_admin_ve_cualquier_reservacion(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_otro_cliente_recibe_403(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_muestra_duracion_de_estancia(self):
        # JUE→SAB = 2 noches
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertContains(response, "2 noche(s)")
        self.assertEqual(response.context["duracion"], 2)


# ---------------------------------------------------------------------------
# Management command: finalizar_reservaciones
# ---------------------------------------------------------------------------

from datetime import date as _date
from io import StringIO

from django.core.management import call_command


class FinalizarReservacionesCommandTests(TestCase):

    def setUp(self):
        parque = crear_parque()
        self.hospedaje = crear_hospedaje(parque)
        self.cliente = crear_cliente()

    def _reservacion(self, fecha_inicio, fecha_fin,
                     estado=Reservacion.EstadoReservacion.ACTIVA):
        r = Reservacion.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            num_huespedes=1,
            unidades_reservadas=1,
            precio_total=Decimal("800.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )
        if estado != Reservacion.EstadoReservacion.ACTIVA:
            r.estado = estado
            r.save()
        return r

    def _call(self, **kwargs):
        out = StringIO()
        call_command("finalizar_reservaciones", stdout=out, **kwargs)
        return out.getvalue()

    def test_finaliza_reservaciones_pasadas(self):
        r = self._reservacion(_date(2026, 5, 1), _date(2026, 5, 5))
        self._call()
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.EstadoReservacion.FINALIZADA)

    def test_no_finaliza_reservaciones_futuras(self):
        r = self._reservacion(JUE, SAB)   # futuras (jun-2026)
        self._call()
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.EstadoReservacion.ACTIVA)

    def test_no_toca_reservaciones_canceladas_pasadas(self):
        r = self._reservacion(
            _date(2026, 5, 1), _date(2026, 5, 5),
            estado=Reservacion.EstadoReservacion.CANCELADA,
        )
        self._call()
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_no_toca_reservaciones_ya_finalizadas(self):
        r = self._reservacion(
            _date(2026, 5, 1), _date(2026, 5, 5),
            estado=Reservacion.EstadoReservacion.FINALIZADA,
        )
        self._call()
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.EstadoReservacion.FINALIZADA)

    def test_finaliza_multiples_en_lote(self):
        r1 = self._reservacion(_date(2026, 4, 1), _date(2026, 4, 5))
        r2 = self._reservacion(_date(2026, 4, 10), _date(2026, 4, 14))
        self._call()
        r1.refresh_from_db()
        r2.refresh_from_db()
        self.assertEqual(r1.estado, Reservacion.EstadoReservacion.FINALIZADA)
        self.assertEqual(r2.estado, Reservacion.EstadoReservacion.FINALIZADA)

    def test_dry_run_no_aplica_cambios(self):
        r = self._reservacion(_date(2026, 5, 1), _date(2026, 5, 5))
        output = self._call(dry_run=True)
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.EstadoReservacion.ACTIVA)
        self.assertIn("dry-run", output)

    def test_mensaje_cuando_no_hay_pendientes(self):
        output = self._call()
        self.assertIn("No hay reservaciones por finalizar", output)

    def test_mensaje_de_exito_con_conteo(self):
        self._reservacion(_date(2026, 5, 1), _date(2026, 5, 5))
        output = self._call()
        self.assertIn("1 reservación(es)", output)


# ---------------------------------------------------------------------------
# Integración: detalle_parque muestra disponibilidad real y links de reserva
# ---------------------------------------------------------------------------

class DetalleParqueIntegracionTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque, unidades=5)
        self.cliente = crear_cliente()

    def _url(self):
        return reverse("detalle_parque", args=[self.parque.id])

    def test_template_muestra_link_de_reservar(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        expected_url = reverse("crear_reservacion", args=[self.hospedaje.id])
        self.assertContains(response, expected_url)

    def test_template_muestra_disponibilidad_en_contexto(self):
        response = self.client.get(self._url())
        self.assertIn("disponibilidad", response.context)
        self.assertIn(self.hospedaje.id, response.context["disponibilidad"])

    def test_disponibilidad_refleja_reservaciones_activas(self):
        # Ocupa 3 de 5 unidades con fecha_inicio=hoy
        from datetime import date as _date
        hoy = _date.today()
        Reservacion.objects.create(
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=1),
            num_huespedes=2,
            unidades_reservadas=3,
            precio_total=Decimal("2400.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )
        response = self.client.get(self._url())
        disponibles = response.context["disponibilidad"][self.hospedaje.id]
        self.assertEqual(disponibles, 2)

    def test_disponibilidad_no_cuenta_reservaciones_canceladas(self):
        from datetime import date as _date
        hoy = _date.today()
        r = Reservacion.objects.create(
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=1),
            num_huespedes=2,
            unidades_reservadas=5,
            precio_total=Decimal("4000.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )
        r.estado = Reservacion.EstadoReservacion.CANCELADA
        r.save()
        response = self.client.get(self._url())
        self.assertEqual(response.context["disponibilidad"][self.hospedaje.id], 5)
