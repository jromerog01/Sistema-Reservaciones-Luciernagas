"""
Management command: finalizar_reservaciones

Marca como FINALIZADA toda reservación ACTIVA cuya fecha_fin
sea anterior a hoy. Se diseña para ejecutarse diariamente
(p. ej. mediante cron o Celery beat).

Uso:
    python manage.py finalizar_reservaciones
    python manage.py finalizar_reservaciones --dry-run
"""
from datetime import date

from django.core.management.base import BaseCommand

from reservaciones.models import Reservacion


class Command(BaseCommand):
    help = "Finaliza reservaciones activas cuya fecha de salida ya pasó."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra cuántas reservaciones se finalizarían sin aplicar cambios.",
        )

    def handle(self, *args, **options):
        hoy = date.today()
        dry_run = options["dry_run"]

        pendientes = Reservacion.objects.filter(
            estado=Reservacion.EstadoReservacion.ACTIVA,
            fecha_fin__lt=hoy,
        )

        total = pendientes.count()

        if total == 0:
            self.stdout.write("No hay reservaciones por finalizar.")
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Se finalizarían {total} reservación(es)."
                )
            )
            return

        actualizadas = pendientes.update(
            estado=Reservacion.EstadoReservacion.FINALIZADA
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Se finalizaron {actualizadas} reservación(es) con fecha de salida anterior a {hoy}."
            )
        )
