from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from ....models import Expediente
from ....constants.solicitudes.estados import EstadosSolicitud
class RecepcionMesaDePartesChangeExpedienteArchivoAnexoPermission(BasePermission):
    """
    Permite modificar, actualizar o eliminar anexos de expedientes de Mesa de Partes
    solo si:
      1. La solicitud vinculada al expediente NO está finalizada.
      2. El usuario que intenta modificar el anexo es quien creó el expediente.
      3. La solicitud (si existe) se encuentra en los estados permitidos para Supervisores.
      4. Si el expediente no está vinculado a ninguna solicitud, se permite cambios.
    """
    def has_object_permission(self, request, view, obj):
        if view.action not in ["update", "partial_update", "destroy"]:
            return True

        expediente = getattr(obj, "expediente", None)
        if not expediente:
            raise PermissionDenied("El anexo no está vinculado a un expediente válido.")

        solicitud = getattr(expediente, "solicitud", None)

        # 1️⃣ Si hay solicitud finalizada, bloquear
        if solicitud and getattr(solicitud, "finalizado", False):
            raise PermissionDenied("La solicitud vinculada está finalizada y no se puede modificar este anexo.")

        # 2️⃣ Solo el creador del expediente puede cambiar
        if expediente.creado_por != request.user:
            raise PermissionDenied("Solo el usuario que creó el expediente puede modificar este anexo.")

        # 3️⃣ Validar estados permitidos si hay solicitud
        if solicitud and solicitud.estado not in EstadosSolicitud.MESA_DE_PARTES_EDITABLES:
            raise PermissionDenied(
                f"No puedes modificar la solicitud porque el estado '{solicitud.estado}' no está permitido para Recepción Mesa de Partes."
            )

        return True


class RecepcionMesaDePartesViewExpedienteArchivoAnexoPermission(BasePermission):
    """
    Permite ver anexos sin restricciones.
    """
    def has_object_permission(self, request, view, obj):
        return True


class RecepcionMesaDePartesCreateExpedienteArchivoAnexoPermission(BasePermission):
    """
    Bloquea creación de anexos si:
      - El expediente no existe
      - La solicitud vinculada está finalizada
      - La solicitud no está en un estado permitido
      - El usuario no es quien creó el expediente
    """
    def has_permission(self, request, view):
        if view.action != "create":
            return True

        expediente_id = request.data.get("expediente")
        if not expediente_id:
            raise PermissionDenied("Debes indicar el expediente para este anexo.")

        try:
            expediente = Expediente.objects.get(id=expediente_id)
        except Expediente.DoesNotExist:
            raise PermissionDenied("Expediente no encontrado.")

        # Debe ser el creador del expediente
        if expediente.creado_por != request.user:
            raise PermissionDenied("Solo el usuario que creó el expediente puede agregar anexos.")

        solicitud = getattr(expediente, "solicitud", None)

        # Si no hay solicitud, se permite
        if not solicitud:
            return True

        # No debe estar finalizada
        if solicitud.finalizado:
            raise PermissionDenied("No se pueden crear anexos para solicitudes finalizadas.")

        # Debe estar en un estado permitido
        if solicitud.estado not in EstadosSolicitud.MESA_DE_PARTES_EDITABLES:
            raise PermissionDenied(
                f"No puedes crear anexos porque la solicitud está en el estado '{solicitud.estado}', que no está permitido."
            )

        return True


class RecepcionMesaDePartesExpedienteArchivoAnexoPermission(BasePermission):
    """
    Combina permisos para los anexos de Mesa de Partes
    """
    def has_permission(self, request, view):
        return RecepcionMesaDePartesCreateExpedienteArchivoAnexoPermission().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        # Ver anexos siempre permitido
        RecepcionMesaDePartesViewExpedienteArchivoAnexoPermission().has_object_permission(request, view, obj)

        # Cambios solo si solicitud no finalizada
        RecepcionMesaDePartesChangeExpedienteArchivoAnexoPermission().has_object_permission(request, view, obj)

        return True
