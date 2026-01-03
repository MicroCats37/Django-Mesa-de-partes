from django.apps import AppConfig


class MesaDePartesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mesa_de_partes'

class TuAppConfig(AppConfig):
    name = 'mesa_de_partes'

    def ready(self):
        import mesa_de_partes.signals