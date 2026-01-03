from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from common.utils.constants.solicitudes.estados import EstadosSolicitud

class FieldPermission(BasePermission):
    """
    Permite modificar solo ciertos campos de la solicitud según
    el rol del usuario y el estado permitido.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # 🔹 Si la solicitud ya está finalizada, nadie puede modificarla
        if getattr(obj, "finalizado", False):
            raise PermissionDenied("Esta solicitud ya está finalizada y no puede modificarse.")

        # 🔹 Mesa de Partes
        if user.groups.filter(name="Mesa de Partes").exists():
            # Solo puede crear solicitudes con estados específicos
            if view.action in ["create"]:
                estado = request.data.get("estado")
                if estado not in EstadosSolicitud.MESA_DE_PARTES_EDITABLES_ESTADOS:
                    raise PermissionDenied(
                        f"No puedes asignar el estado '{estado}' al crear la solicitud como Mesa de Partes."
                    )

        # 🔹 Supervisor
        if user.groups.filter(name="Supervisor").exists():
            if view.action in ["update", "partial_update"]:
                # Solo puede cambiar los campos 'estado' y 'usuario_asignado'
                campos_permitidos = {"estado", "usuario_asignado"}
                if set(request.data.keys()) - campos_permitidos:
                    raise PermissionDenied("Solo puedes cambiar los campos 'estado' y 'usuario_asignado'.")

                # Validar que el estado está permitido
                estado = request.data.get("estado", obj.estado)
                if estado not in EstadosSolicitud.SUPERVISOR_EDITABLES_ESTADOS:
                    raise PermissionDenied(f"No puedes asignar el estado '{estado}' como Supervisor.")

        # 🔹 Área Encargada
        if user.groups.filter(name="Area Encargada").exists():
            if view.action in ["update", "partial_update"]:
                # Solo puede cambiar 'estado' y 'finalizado'
                campos_permitidos = {"estado", "usuario_asignado", "finalizado"}
                if set(request.data.keys()) - campos_permitidos:
                    raise PermissionDenied("Solo puedes cambiar los campos 'usuario_asignado' , 'estado' y 'finalizado'.")

                # Validar que el estado está permitido para Área Encargada
                estado = request.data.get("estado", obj.estado)
                if estado not in EstadosSolicitud.AREA_ENCARGADA_EDITABLES_ESTADOS:
                    raise PermissionDenied(f"No puedes asignar el estado '{estado}' como Área Encargada.")

                # Validar finalizado
                if "finalizado" in request.data and request.data.get("finalizado") is not True:
                    raise PermissionDenied("El campo 'finalizado' solo puede establecerse en True.")

        return True
