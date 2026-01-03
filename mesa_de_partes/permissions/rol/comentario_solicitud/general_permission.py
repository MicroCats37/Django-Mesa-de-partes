from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from mesa_de_partes.models import Solicitud


class ComentarioSolicitudPermission(BasePermission):
    """
    Permisos para Comentarios de Solicitud

    REGLAS:
    - Solo se permite CREATE
    - No se permite UPDATE / PATCH / DELETE
    - Solo pueden comentar:
        * Creador de la solicitud
        * Usuario asignado
        * Usuarios adjuntados
        * Supervisores
    - No se puede comentar si la solicitud está finalizada
    """

    # ------------------------------------------------------------------
    # PERMISOS A NIVEL DE VISTA
    # ------------------------------------------------------------------
    def has_permission(self, request, view):
        action = view.action

        # ❌ Bloquear modificaciones
        if action in ["update", "partial_update", "destroy"]:
            return False

        # ✔ Validar CREATE aquí (DRF no ejecuta object_permission en create)
        if action == "create":
            return self.check_create(request)

        # ✔ retrieve / list permitidos
        return True

    # ------------------------------------------------------------------
    # PERMISOS A NIVEL DE OBJETO
    # ------------------------------------------------------------------
    def has_object_permission(self, request, view, obj):
        # CREATE no pasa por aquí en DRF
        return True

    # ==================================================================
    # 🔥 VALIDACIÓN DE CREACIÓN DE COMENTARIO
    # ==================================================================
    def check_create(self, request):
        """
        Validaciones para crear comentario:
        - Solicitud no finalizada
        - Usuario autorizado a comentar
        """

        user = request.user
        solicitud_id = request.data.get("solicitud")

        if not solicitud_id:
            raise PermissionDenied(
                "Solicitud no especificada."
            )

        try:
            solicitud = Solicitud.objects.select_related(
                "expediente"
            ).get(id=solicitud_id)
        except Solicitud.DoesNotExist:
            raise PermissionDenied(
                "Solicitud no válida."
            )

        # 1️⃣ No permitir comentar si la solicitud está finalizada
        if solicitud.finalizado:
            raise PermissionDenied(
                "No puedes comentar en una solicitud finalizada."
            )

        # 2️⃣ Usuario creador de la solicitud
        if solicitud.expediente.creado_por == user:
            return True

        # 3️⃣ Usuario asignado
        if solicitud.usuario_asignado == user:
            return True

        # 4️⃣ Usuario adjuntado a la solicitud
        if solicitud.usuario_solicitud_adjuntado.filter(usuario=user).exists():
            return True

        # 5️⃣ Supervisor
        if user.groups.filter(name="Supervisor Mesa de Partes").exists():
            return True

        # ❌ Si no cumple nada
        raise PermissionDenied(
            "No tienes permiso para comentar en esta solicitud."
        )
