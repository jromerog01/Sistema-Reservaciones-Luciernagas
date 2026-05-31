from django.test import TestCase

from usuarios.forms import RegistroForm


class RegistroFormTests(TestCase):
    """Verifica los datos obligatorios solicitados al registrar clientes."""

    def datos_validos(self, **cambios):
        datos = {
            "username": "cliente-nuevo",
            "first_name": "Ana",
            "last_name": "Perez Lopez",
            "email": "ana@example.com",
            "password1": "ClaveSegura_2026!",
            "password2": "ClaveSegura_2026!",
        }
        datos.update(cambios)
        return datos

    def test_nombre_y_apellidos_son_obligatorios(self):
        form = RegistroForm()

        self.assertTrue(form.fields["first_name"].required)
        self.assertTrue(form.fields["last_name"].required)

    def test_rechaza_nombre_vacio(self):
        form = RegistroForm(self.datos_validos(first_name=""))

        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_rechaza_apellidos_vacios(self):
        form = RegistroForm(self.datos_validos(last_name=""))

        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)
