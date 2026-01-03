from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from common.utils.constants.solicitudes.estados import EstadosSolicitud


def es_mesa_de_partes(user):
    return user.groups.filter(name="Recepcion Mesa de Partes").exists()


# Estados que permiten editar cuando el expediente ya está asociado a una solicitud
ESTADOS_PERMITIDOS_EDITAR = EstadosSolicitud.MESA_DE_PARTES_EDITABLES


class MesaDePartesExpedientePermission(BasePermission):
    """
    Permiso para controlar edición de expedientes por Mesa de Partes.
    
    Reglas:
    - GET siempre permitido.
    - Solo usuarios Mesa de Partes pueden editar.
    - Solo puede editar si:
        1. El expediente NO está asociado a ninguna solicitud
        2. O está asociado a una solicitud pero su estado pertenece
           a ESTADOS_PERMITIDOS_EDITAR.
    """

    def has_permission(self, request, view):
        # GET, HEAD, OPTIONS permitidos siempre
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Cualquier otra acción requiere ser Mesa de Partes
        if not es_mesa_de_partes(request.user):
            raise PermissionDenied("Solo Mesa de Partes puede modificar expedientes.")

        return True

    def has_object_permission(self, request, view, obj):
        # Permitir lectura
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Validar que sea Mesa de Partes
        if not es_mesa_de_partes(request.user):
            raise PermissionDenied("No tienes permisos para modificar este expediente.")

        # Verificar si el expediente tiene solicitudes asociadas
        solicitud = getattr(obj, "solicitud", None)

        # 🔹 Caso 1: SI NO TIENE SOLICITUD, puede editar
        if solicitud is None:
            return True

        # 🔹 Caso 2: SI TIENE SOLICITUD → validar estado
        if solicitud.estado not in ESTADOS_PERMITIDOS_EDITAR:
            raise PermissionDenied(
                f"No puedes editar un expediente asociado a una solicitud en estado '{solicitud.estado}'."
            )

        return True
