from rest_framework.permissions import DjangoModelPermissions
from rest_framework.exceptions import PermissionDenied

class DjangoModelPermissionsConMensaje(DjangoModelPermissions):

    # Mapear acciones de DRF a permisos de Django
    accion_map = {
        "list": "view",
        "retrieve": "view",
        "create": "add",
        "update": "change",
        "partial_update": "change",
        "destroy": "delete"
    }

    def has_permission(self, request, view):
        # Primero, verificar autenticación
        if not request.user.is_authenticated:
            raise PermissionDenied("Debes estar autenticado para realizar esta acción.")

        # Obtener la acción
        accion = self.accion_map.get(view.action)
        if not accion:
            # Si la acción no está mapeada, permitir por defecto
            return True

        # Obtener modelo y app
        model_class = getattr(view, "queryset", None)
        if model_class is None:
            return True  # No hay queryset definido, no se valida

        model_name = model_class.model._meta.model_name
        app_label = model_class.model._meta.app_label

        # Generar codename dinámico
        permiso_codename = f"{app_label}.{accion}_{model_name}"

        # Validar el permiso
        if not request.user.has_perm(permiso_codename):
            # Mensaje personalizado según la acción
            accion_lectura = {
                "add": "crear",
                "change": "modificar",
                "delete": "eliminar",
                "view": "ver"
            }
            mensaje_accion = accion_lectura.get(accion, accion)
            raise PermissionDenied(
                f"No tienes permiso para {mensaje_accion} {model_class.model._meta.verbose_name}."
            )

        return True
