from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from common.utils.constants.solicitudes.estados import EstadosSolicitud


class EncargadoAreaSolicitudPermission(BasePermission):
    """
    Permisos modulares para Encargado de Área:

    REGLAS:
    - No pueden crear solicitudes
    - Solo pueden modificar solicitudes asignadas a ellos
    - Solo pueden modificar si la solicitud NO está finalizada
    - Solo pueden modificar campos permitidos
    - El estado de la solicitud debe estar en los estados permitidos
    """

    CAMPOS_PERMITIDOS = {"estado", "usuario_asignado", "finalizado","usuarios_adjuntados","archivos_anexados","archivos_anexados_descripciones"}

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE VISTA (sin objeto)
    # ----------------------------------------------------------------------
    def has_permission(self, request, view):
        """
        Aquí controlamos:
        - No permitir create
        - Opcional: bloquear delete
        """
        action = view.action
        
        if action == "create":
            return False

        
        if action == "destroy":
            return False

        return True

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE OBJETO (update, patch, etc.)
    # ----------------------------------------------------------------------
    def has_object_permission(self, request, view, obj):
        action = view.action

        if action in ["update", "partial_update"]:
            return self.check_update(request, view, obj)

        # Para retrieve, list, etc.
        return True

    # ======================================================================
    #  🔥 FUNCIÓN MODULAR: VALIDAR UPDATE / PATCH
    # ======================================================================
    def check_update(self, request, view, obj):
        """
        Reglas completas para que el Encargado de Área pueda modificar:
        - Debe ser el usuario asignado
        - La solicitud no debe estar finalizada
        - Campos enviados deben ser permitidos
        - Estado actual debe permitir modificación
        - Solo puede finalizar cuando el estado es CERRADO
        """

        user = request.user

        # 1️⃣ Debe ser el usuario asignado
        if obj.usuario_asignado != user:
            raise PermissionDenied("Solo el usuario asignado puede modificar esta solicitud.")

        # 2️⃣ No modificar si está finalizada
        if obj.finalizado:
            raise PermissionDenied("La solicitud ya está finalizada y no puede modificarse.")

        # 3️⃣ Validar campos permitidos
        campos_enviados = set(request.data.keys())
        campos_invalidos = campos_enviados - self.CAMPOS_PERMITIDOS

        if campos_invalidos:
            raise PermissionDenied(
                f"Solo puedes modificar los campos: {', '.join(self.CAMPOS_PERMITIDOS)}"
            )

        # 4️⃣ Validar estado actual
        if obj.estado not in EstadosSolicitud.AREA_ENCARGADA_EDITABLES:
            raise PermissionDenied(
                f"No puedes modificar una solicitud cuyo estado actual es '{obj.estado}'."
            )

        # 5️⃣ El nuevo estado debe ser permitido
        nuevo_estado = request.data.get("estado")
        if nuevo_estado and nuevo_estado not in EstadosSolicitud.AREA_ENCARGADA:
            raise PermissionDenied(
                f"No puedes usar el estado '{nuevo_estado}' para Encargado de Área."
            )

        # 6️⃣ VALIDACIÓN FINALIZADO ⇄ ESTADO
        finalizado = request.data.get("finalizado")
        finalizado_raw = request.data.get("finalizado")
        finalizado = str(finalizado_raw).lower() in ["true", "1", "yes"]

        # ❌ No se puede finalizar si el estado NO es CERRADO
        if finalizado is True and nuevo_estado != "CERRADO":
            raise PermissionDenied(
                "Solo puedes marcar la solicitud como finalizada cuando el estado es CERRADO."
            )

    

        return True
