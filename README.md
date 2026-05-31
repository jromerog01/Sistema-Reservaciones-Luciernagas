<div style="text-align: left;">
  <img width="200" src="https://www.fciencias.unam.mx/sites/default/files/logoFC_2.png" alt="Logo FC">
</div>

# Sistema de Reservaciones para el Festival de Luciérnagas

## Ingeniería de Software 2026-2

Proyecto final desarrollado con Django para consultar parques participantes del Festival de Luciérnagas, explorar sus servicios y hospedajes, visualizar su ubicación en un mapa interactivo y crear reservaciones con reglas de disponibilidad, temporada y permisos de usuario.

El sistema está pensado para varios tipos de uso:

- **Visitantes**: pueden consultar la página de inicio, explorar parques, usar filtros y revisar el mapa.
- **Clientes** autenticados: pueden registrarse, iniciar sesión, editar su perfil, crear reservaciones, consultar sus reservaciones y cancelarlas.
- **Administradores**: pueden gestionar parques, servicios, hospedajes, usuarios administradores y consultar todas las reservaciones.

## Equipo: `<404> Team Not Found`

**Alumnos:**

| Nombre Completo              | Número de cuenta |
|------------------------------| --- |
| Chávez Martínez Marco Antonio | 320328594 |
| Cruz Campos Pablo Isaías     | 424022084 |
| Romero Godoy Jesús Antonio   | 321144292 |
| Trejo Maya Diego Alexander   | 424033338 |
| Vega Alonso Diego Hazael     | 321301183 |

## Tecnologías principales

- Python 3.12.8
- Django 6.0.1
- SQLite para desarrollo
- django-allauth para autenticación social con Google
- django-crispy-forms y crispy-bootstrap5
- django-environ para variables de entorno
- Leaflet/OpenStreetMap para el mapa interactivo
- Tailwind CSS por CDN en varias plantillas

## Estructura del proyecto

```text
proyectoLuciernagas/
├── manage.py
├── environment.yml
├── db.sqlite3
├── proyectoLuciernagas/        # Configuración global, URLs y vistas de inicio/mapa
├── usuarios/                   # Usuario personalizado, login, registro y perfiles
├── parques/                    # Parques, servicios, hospedajes, mapa y catálogo
├── reservaciones/              # Creación, validación, cancelación y consulta de reservas
└── static/                     # CSS, JavaScript e imágenes del sitio
```

## Aplicaciones del sistema

### `usuarios`

Maneja la identidad y los permisos del sistema.

- Define un modelo `Usuario` personalizado basado en `AbstractUser`.
- Usa correo único y permite autenticar con usuario o correo electrónico.
- Maneja roles explícitos: `CLIENTE` y `ADMINISTRADOR`.
- Incluye registro, inicio de sesión, cierre de sesión y edición de perfil.
- Permite que usuarios staff creen otros administradores desde la interfaz del sistema.
- Integra django-allauth para habilitar inicio de sesión con Google cuando existen credenciales en `.env`.

### `parques`

Centraliza la información de los parques participantes.

- Modelo `Parque`: nombre, estado, dirección, coordenadas, horario, descripción y servicios.
- Modelo `Servicio`: servicios ofrecidos por los parques.
- Modelo `Hospedaje`: opciones de hospedaje por parque, actualmente `CABAÑA` y `CAMPING`.
- Catálogo público de parques con filtros por estado, hospedaje y servicios.
- Vista de detalle con galería, hospedajes disponibles, servicios y enlace a Google Maps.
- Panel de administración con filtros personalizados y sincronización del hospedaje base de camping.

El mapa usa un patrón Adapter:

- `MapaAdapter`: contrato común para convertir parques a marcadores.
- `OpenStreetMapAdapter`: formato usado por Leaflet/OpenStreetMap.
- `GoogleMapsAdapter`: alternativa preparada para una posible integración con Google Maps.
- `MapaService`: obtiene parques con sus relaciones y delega la conversión al adapter configurado.

### `reservaciones`

Contiene la lógica principal de reservas.

- Modelo `Reservacion`: fechas, huéspedes, unidades reservadas, precio total, estado, hospedaje y usuario.
- Estados posibles: `ACTIVA`, `CANCELADA` y `FINALIZADA`.
- Formulario con validaciones de fechas, temporada, martes de mantenimiento, capacidad y disponibilidad.
- Vistas para crear, cancelar, consultar detalle, ver reservaciones propias y ver todas las reservaciones como administrador.
- Comando de mantenimiento para finalizar reservas vencidas.

También aplica patrones de diseño:

- **Facade**: `ReservacionFacade` ofrece una API simple para crear y cancelar reservaciones.
- **Template Method**: `ReservacionTemplate` define el flujo general de creación y `ReservacionHospedajeTemplate` agrega reglas específicas de hospedaje.
- **Observer**: `ReservacionNotificador` avisa a observadores cuando una reserva se crea o cancela.

## Reglas de reservación

Las reservas no se guardan directamente desde la vista: pasan por el formulario, el facade y el template de reservación. Las reglas implementadas son:

- La fecha de llegada no puede estar en el pasado.
- La fecha de salida debe ser posterior a la fecha de llegada.
- La estancia debe caer dentro de la temporada del festival: junio, julio y agosto.
- El checkout del 1 de septiembre es válido si la última noche fue el 31 de agosto.
- La estancia no puede incluir noches de martes, porque se consideran días de mantenimiento.
- El checkout en martes sí puede ser válido si ninguna noche reservada cae en martes.
- La estancia máxima para hospedaje es de 30 noches.
- Las unidades reservadas deben cubrir la cantidad de huéspedes según la capacidad por unidad.
- No se permite sobre-reservar unidades cuando ya hay reservaciones activas en el mismo periodo.
- Las reservaciones canceladas no cuentan como ocupación.
- El precio se calcula por unidades, precio por unidad y número de noches.
- Las reservaciones en temporada reciben un recargo del 20%.

## URL's principales

| Ruta | Descripción |
| --- | --- |
| `/` o `/inicio/` | Página principal con carrusel, mapa resumido, hospedajes y reserva rápida |
| `/inicio/mapa/` | Mapa interactivo completo |
| `/parques/` | Listado público de parques |
| `/parques/<id>/` | Detalle de un parque |
| `/usuarios/registro/` | Registro de usuarios |
| `/usuarios/login/` | Inicio de sesión |
| `/usuarios/perfil/` | Perfil del usuario autenticado |
| `/usuarios/admins/` | Lista de administradores, solo staff |
| `/usuarios/admins/nuevo/` | Creación de administrador, solo staff |
| `/reservaciones/nueva/<hospedaje_id>/` | Crear reservación |
| `/reservaciones/mis-reservaciones/` | Reservaciones del usuario autenticado |
| `/reservaciones/todas/` | Todas las reservaciones, solo administradores |
| `/reservaciones/<id>/` | Detalle de una reservación |
| `/reservaciones/<id>/cancelar/` | Cancelar reservación |
| `/admin/` | Panel administrativo de Django |

## Instalación y ejecución local

### 1. Crear el ambiente de Conda

```shell
conda env create -f environment.yml
conda activate proyectoFinal-404TeamNotFound
```

### 2. Configurar variables de entorno

El proyecto usa `django-environ` y lee variables desde `.env`. Se incluye `.env.example` como plantilla:

```shell
cp .env.example .env
```

Variables principales:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

GOOGLE_OAUTH_CLIENT_ID=tu_google_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=tu_google_oauth_client_secret

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=app-password-de-gmail
DEFAULT_FROM_EMAIL=Luciernagas <tu_correo@gmail.com>
```

Google OAuth y el envío real de correos son opcionales para desarrollo. Si no se configuran credenciales de correo, Django usa el backend de consola definido en `settings.py`.


### 3. Levantar el servidor

```shell
python manage.py runserver
```

La aplicación queda disponible en:

```text
http://127.0.0.1:8000/
```

## Comandos útiles

Ejecutar pruebas:

```shell
python manage.py test
```

Ejecutar solo pruebas de parques y reservaciones:

```shell
python manage.py test parques reservaciones
```

Revisar qué reservaciones activas ya deberían finalizarse:

```shell
python manage.py finalizar_reservaciones --dry-run
```

Finalizar reservaciones activas cuya fecha de salida ya pasó:

```shell
python manage.py finalizar_reservaciones
```

## Cobertura de pruebas

Actualmente hay pruebas enfocadas en:

- Conversión de parques a marcadores para el mapa.
- Servicio de mapa con adapter inyectable.
- Filtros y datos del mapa interactivo.
- Listado y detalle de parques.
- Cálculo de noches, unidades necesarias y precio.
- Validación de temporada junio-agosto.
- Bloqueo de noches en martes.
- Disponibilidad por solapamiento de reservaciones activas.
- Creación de reservaciones desde vistas.
- Permisos para cancelar, consultar reservaciones propias y consultar todas las reservaciones.
- Finalización de reservaciones vencidas mediante comando de mantenimiento.

## Notas de desarrollo

- La zona horaria configurada es `America/Mexico_City`.
- El idioma configurado es `es-mx`.
- El modelo de usuario activo es `usuarios.Usuario`.
- Los archivos estáticos viven en `static/`.
- Las plantillas globales viven en `proyectoLuciernagas/templates/`.
- Las plantillas específicas de cada app viven dentro de `templates/` en su respectiva aplicación.
- El archivo `.env` está ignorado por Git y no debe subirse con credenciales reales.
