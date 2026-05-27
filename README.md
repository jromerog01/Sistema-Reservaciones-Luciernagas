<div style="text-align: left;">
  <img width="200" src="https://www.fciencias.unam.mx/sites/default/files/logoFC_2.png" alt="Logo FC">
</div>

# Sistema de Reservaciones Festival de Luciernagas

Equipo: 404 - Team Not Found

Integrantes:

- Chavez Martinez Marco Antonio
- Cruz Campos Pablo Isaias
- Romero Godoy Jesus Antonio
- Trejo Maya Diego Alexander
- Vega Alonso Diego Hazael

## Proposito

Este proyecto implementa un sistema web para centralizar la informacion de los parques oficiales del Festival Internacional de las Luciernagas 2026 y permitir que los visitantes realicen reservaciones de hospedaje en cabanas o zonas de camping.

El sistema busca resolver tres problemas principales:

- Dificultad para localizar parques oficiales y consultar su informacion.
- Sobrecarga administrativa por reservaciones gestionadas manualmente.
- Riesgo de sobre-reservaciones por falta de control de disponibilidad.

## Alcance Funcional

El sistema contempla dos tipos de usuario:

- Cliente: puede registrarse, iniciar sesion, cerrar sesion, consultar el mapa,
  realizar reservaciones, consultar sus reservaciones y cancelarlas.
- Administrador: puede gestionar parques, servicios, hospedajes y consultar todas
  las reservaciones realizadas.

Funciones principales:

- Registro e inicio de sesion de usuarios.
- Mapa interactivo con marcadores de parques oficiales.
- Consulta de informacion de cada parque: nombre, direccion, servicios, horario y
  hospedajes disponibles.
- Reservacion de hospedaje por fecha, numero de personas y tipo de visita.
- Validacion de reglas de negocio del festival.
- Envio de correos de confirmacion y cancelacion.
- Panel administrativo basado en Django Admin.

## Reglas de Negocio

- Las reservaciones solo se permiten durante junio, julio y agosto.
- No se pueden reservar estancias que incluyan martes, porque ese dia se reserva
  para mantenimiento.
- Todos los parques deben contar con zona de camping.
- Algunos parques pueden contar con cabanas.
- El sistema debe validar disponibilidad para evitar sobre-reservaciones.
- Una reservacion activa ocupa unidades de hospedaje durante el rango de fechas
  seleccionado.
- Una reservacion cancelada deja de contar para la disponibilidad.

## Arquitectura

El proyecto usa Django y sigue el patron MVT:

- Model: entidades persistentes del dominio.
- View: logica de peticiones HTTP, validaciones y coordinacion.
- Template: interfaz HTML renderizada para usuarios y administradores.

Modulos principales:

- `usuarios`: registro, autenticacion y roles de usuario.
- `parques`: parques, servicios, hospedajes y datos para el mapa.
- `reservaciones`: creacion, consulta, cancelacion y reglas de reserva.

## Modelo de Datos

Entidades principales:

- `Usuario`: usuario autenticable con rol `CLIENTE` o `ADMINISTRADOR`.
- `Parque`: parque oficial con direccion, estado, coordenadas, horarios y servicios.
- `Servicio`: servicio disponible en uno o mas parques.
- `Hospedaje`: tipo de alojamiento de un parque, como cabana o camping.
- `Reservacion`: estancia registrada por un usuario sobre un hospedaje concreto.


## Patrones de Diseno Aplicados

- Adapter: adapta los datos internos de `Parque` al formato requerido por el mapa
  interactivo. Implementado en `parques/mapa_adapters.py`.
- Observer: separa los eventos de reservacion del envio de correos. Implementado
  en `reservaciones/notificador.py` y `reservaciones/utils/observers.py`.
- Template Method: define el flujo general para procesar reservaciones. Implementado en `reservaciones/utils/template_method.py`.


## Instalacion y Ejecucion

Crear el ambiente con Miniconda:

```bash
conda env create -f environment.yml
conda activate proyectoLuciernagas
```


Crear superusuario:

```bash
python manage.py createsuperuser
```

Levantar servidor local:

```bash
python manage.py runserver
```

Rutas principales:

- `/inicio/`: pagina de inicio.
- `/inicio/mapa/`: mapa interactivo.
- `/parques/`: listado de parques.
- `/usuarios/registro/`: registro de cliente.
- `/usuarios/login/`: inicio de sesion.
- `/usuarios/logout/`: cierre de sesion.
- `/reservaciones/`: modulo de reservaciones.
- `/admin/`: panel administrativo.

## Pruebas

El proyecto incluye pruebas en:

- `reservaciones/tests.py`
- `parques/tests.py`
- `usuarios/tests.py`

Ejecutar:

```bash
python manage.py test
```

Las pruebas cubren principalmente:

- Calculo de duracion de reservacion.
- Calculo de unidades necesarias.
- Validacion de temporada junio-agosto.
- Bloqueo de martes.
- Disponibilidad y sobre-reservaciones.
- Creacion, consulta y cancelacion de reservaciones.
- Adaptacion de marcadores para mapa.