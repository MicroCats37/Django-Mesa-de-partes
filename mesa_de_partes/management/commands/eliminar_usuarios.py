from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Elimina todos los usuarios excepto admin"

    def handle(self, *args, **kwargs):
        usuarios = User.objects.exclude(is_superuser=True)
        count = usuarios.count()
        usuarios.delete()
        self.stdout.write(self.style.SUCCESS(f"Se eliminaron {count} usuarios (excepto admin)."))
