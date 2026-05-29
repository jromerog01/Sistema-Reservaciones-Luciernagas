from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Usuario

@receiver(pre_save, sender=Usuario)
def sincronizar_admin_django(sender, instance, **kwargs):
    """
    Sincroniza el rol ADMINISTRADOR con el acceso is_staff de Django
    sin modificar la definición del modelo.
    """
    if instance.rol == Usuario.Rol.ADMINISTRADOR:
        instance.is_staff = True
    elif instance.rol == Usuario.Rol.CLIENTE and not instance.is_superuser:
        instance.is_staff = False
