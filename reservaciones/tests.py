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
        username=username,
        email=email,
        password="pass1234",
        rol=Usuario.Rol.CLIENTE,
    )


def crear_admin(username="admin1", email="admin1@test.com"):
    return Usuario.objects.create_user(
        username=username,
        email=email,
        password="pass1234",
        rol=Usuario.Rol.ADMINISTRADOR,
    )


def hoy():
    return date.today()


def mañana():
    return hoy() + timedelta(days=1)


def en_dias(n):
    return hoy() + timedelta(days=n)


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------

class ReservacionModelTests(TestCase):

    def test_calcular_duracion_retorna_dias_entre_fechas(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        cliente = crear_cliente()

        reservacion = Reservacion.objects.create(
            fecha_inicio=en_dias(1),
            fecha_fin=en_dias(4),
            num_huespedes=2,
            unidades_reservadas=1,
            precio_total=Decimal("2400.00"),
            hospedaje=hospedaje,
            usuario=cliente,
        )

        self.assertEqual(reservacion.calcular_duracion(), 3)

    def test_estado_por_defecto_es_activa(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        cliente = crear_cliente()

        reservacion = Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(3),
            num_huespedes=1,
            unidades_reservadas=1,
            precio_total=Decimal("1600.00"),
            hospedaje=hospedaje,
            usuario=cliente,
        )

        self.assertEqual(reservacion.estado, Reservacion.EstadoReservacion.ACTIVA)

    def test_str_incluye_id_y_usuario(self):
        parque = crear_parque()
        hospedaje = crear_hospedaje(parque)
        cliente = crear_cliente()

        reservacion = Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(2),
            num_huespedes=1,
            unidades_reservadas=1,
            precio_total=Decimal("800.00"),
            hospedaje=hospedaje,
            usuario=cliente,
        )

        self.assertIn(str(reservacion.id), str(reservacion))
        self.assertIn(str(cliente), str(reservacion))


# ---------------------------------------------------------------------------
# Vista: crear_reservacion
# ---------------------------------------------------------------------------

class CrearReservacionTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque, unidades=5, capacidad=4, precio="800.00")
        self.cliente = crear_cliente()

    def _url(self):
        return reverse("crear_reservacion", args=[self.hospedaje.id])

    def _post(self, **kwargs):
        datos = {
            "fecha_inicio": mañana().isoformat(),
            "fecha_fin": en_dias(4).isoformat(),
            "num_huespedes": 2,
            "unidades_reservadas": 1,
        }
        datos.update(kwargs)
        return self.client.post(self._url(), datos)

    def test_redirige_a_login_si_no_autenticado(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_get_muestra_formulario(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservaciones/crear_reservacion.html")
        self.assertIn("form", response.context)
        self.assertIn("hospedaje", response.context)

    def test_crea_reservacion_y_redirige_al_detalle(self):
        self.client.force_login(self.cliente)
        response = self._post()
        self.assertEqual(Reservacion.objects.count(), 1)
        reservacion = Reservacion.objects.first()
        self.assertRedirects(response, reverse("detalle_reservacion", args=[reservacion.id]))

    def test_precio_total_calculado_correctamente(self):
        # 1 unidad × $800 × 3 noches = $2,400
        self.client.force_login(self.cliente)
        self._post(
            fecha_inicio=mañana().isoformat(),
            fecha_fin=en_dias(4).isoformat(),
            num_huespedes=1,
            unidades_reservadas=1,
        )
        reservacion = Reservacion.objects.first()
        self.assertEqual(reservacion.precio_total, Decimal("2400.00"))

    def test_error_si_unidades_superan_disponibles(self):
        self.client.force_login(self.cliente)
        response = self._post(unidades_reservadas=10)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 unidades disponibles")
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_error_si_huespedes_superan_capacidad(self):
        self.client.force_login(self.cliente)
        # 1 unidad × 4 capacidad = máx 4 huéspedes
        response = self._post(num_huespedes=10, unidades_reservadas=1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "capacidad máxima")
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_error_si_fecha_fin_igual_a_fecha_inicio(self):
        self.client.force_login(self.cliente)
        response = self._post(
            fecha_inicio=mañana().isoformat(),
            fecha_fin=mañana().isoformat(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_error_si_fecha_inicio_en_el_pasado(self):
        self.client.force_login(self.cliente)
        ayer = hoy() - timedelta(days=1)
        response = self._post(fecha_inicio=ayer.isoformat(), fecha_fin=hoy().isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_reservacion_queda_asociada_al_usuario_autenticado(self):
        self.client.force_login(self.cliente)
        self._post()
        reservacion = Reservacion.objects.first()
        self.assertEqual(reservacion.usuario, self.cliente)


# ---------------------------------------------------------------------------
# Vista: cancelar_reservacion
# ---------------------------------------------------------------------------

class CancelarReservacionTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque)
        self.cliente = crear_cliente()
        self.otro_cliente = crear_cliente(username="otro", email="otro@test.com")
        self.admin = crear_admin()
        self.reservacion = Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(3),
            num_huespedes=1,
            unidades_reservadas=1,
            precio_total=Decimal("1600.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )

    def _url(self):
        return reverse("cancelar_reservacion", args=[self.reservacion.id])

    def test_propietario_puede_cancelar(self):
        self.client.force_login(self.cliente)
        self.client.post(self._url())
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_admin_puede_cancelar_reservacion_de_otro_usuario(self):
        self.client.force_login(self.admin)
        self.client.post(self._url())
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.CANCELADA)

    def test_otro_cliente_no_puede_cancelar(self):
        self.client.force_login(self.otro_cliente)
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 403)
        self.reservacion.refresh_from_db()
        self.assertEqual(self.reservacion.estado, Reservacion.EstadoReservacion.ACTIVA)

    def test_no_se_puede_cancelar_reservacion_ya_cancelada(self):
        self.reservacion.estado = Reservacion.EstadoReservacion.CANCELADA
        self.reservacion.save()
        self.client.force_login(self.cliente)
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solo se pueden cancelar reservaciones activas")

    def test_get_muestra_confirmacion(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservaciones/cancelar_reservacion.html")

    def test_cancelar_redirige_a_mis_reservaciones(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self._url())
        self.assertRedirects(response, reverse("mis_reservaciones"))


# ---------------------------------------------------------------------------
# Vista: mis_reservaciones
# ---------------------------------------------------------------------------

class MisReservacionesTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque)
        self.cliente = crear_cliente()
        self.otro = crear_cliente(username="otro2", email="otro2@test.com")

    def _url(self):
        return reverse("mis_reservaciones")

    def _crear_reservacion(self, usuario):
        return Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(3),
            num_huespedes=1,
            unidades_reservadas=1,
            precio_total=Decimal("1600.00"),
            hospedaje=self.hospedaje,
            usuario=usuario,
        )

    def test_redirige_a_login_si_no_autenticado(self):
        response = self.client.get(self._url())
        self.assertIn("/accounts/login/", response["Location"])

    def test_muestra_solo_reservaciones_del_cliente(self):
        r_propia = self._crear_reservacion(self.cliente)
        self._crear_reservacion(self.otro)
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        reservaciones = list(response.context["reservaciones"])
        self.assertEqual(len(reservaciones), 1)
        self.assertEqual(reservaciones[0].id, r_propia.id)

    def test_muestra_mensaje_si_no_hay_reservaciones(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertContains(response, "No tienes reservaciones registradas")

    def test_muestra_duracion_calculada(self):
        self._crear_reservacion(self.cliente)
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertContains(response, "2 noche(s)")


# ---------------------------------------------------------------------------
# Vista: todas_las_reservaciones
# ---------------------------------------------------------------------------

class TodasLasReservacionesTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque)
        self.cliente = crear_cliente()
        self.admin = crear_admin()

    def _url(self):
        return reverse("todas_las_reservaciones")

    def _crear_reservacion(self):
        return Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(5),
            num_huespedes=2,
            unidades_reservadas=1,
            precio_total=Decimal("3200.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )

    def test_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_admin_puede_ver_todas_las_reservaciones(self):
        self._crear_reservacion()
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservaciones/todas_las_reservaciones.html")
        self.assertEqual(response.context["reservaciones"].count(), 1)

    def test_admin_ve_datos_del_cliente(self):
        self._crear_reservacion()
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertContains(response, str(self.cliente))

    def test_no_autenticado_redirige_a_login(self):
        response = self.client.get(self._url())
        self.assertIn("/accounts/login/", response["Location"])


# ---------------------------------------------------------------------------
# Vista: detalle_reservacion
# ---------------------------------------------------------------------------

class DetalleReservacionTests(TestCase):

    def setUp(self):
        self.parque = crear_parque()
        self.hospedaje = crear_hospedaje(self.parque)
        self.cliente = crear_cliente()
        self.otro = crear_cliente(username="otro3", email="otro3@test.com")
        self.admin = crear_admin()
        self.reservacion = Reservacion.objects.create(
            fecha_inicio=mañana(),
            fecha_fin=en_dias(4),
            num_huespedes=2,
            unidades_reservadas=1,
            precio_total=Decimal("2400.00"),
            hospedaje=self.hospedaje,
            usuario=self.cliente,
        )

    def _url(self):
        return reverse("detalle_reservacion", args=[self.reservacion.id])

    def test_propietario_ve_su_reservacion(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservaciones/detalle_reservacion.html")

    def test_admin_ve_reservacion_de_cualquier_usuario(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_otro_cliente_recibe_403(self):
        self.client.force_login(self.otro)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_muestra_duracion_de_estancia(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self._url())
        # 3 noches
        self.assertContains(response, "3 noche(s)")
        self.assertEqual(response.context["duracion"], 3)
