from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from common.utils.constants.solicitudes.estados import EstadosSolicitud


class SupervisorMesaDePartesSolicitudPermission(BasePermission):
    """
    Permisos modulares para Supervisores de Mesa de Partes:

    REGLAS:
    - No pueden crear solicitudes
    - Solo pueden modificar solicitudes en estados permitidos
    - Solo pueden cambiar campos específicos
    - No pueden finalizar una solicitud
    """

    CAMPOS_PERMITIDOS = {"estado", "usuario_asignado","usuarios_adjuntados"}

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE VISTA
    # ----------------------------------------------------------------------
    def has_permission(self, request, view):
        """
        Supervisores NO pueden crear solicitudes.
        """
        action = view.action
        
        if action == "create":
            return False

        
        if action == "destroy":
            return False
        
        return True

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE OBJETO (update, patch)
    # ----------------------------------------------------------------------
    def has_object_permission(self, request, view, obj):
        """
        Supervisa y delega la validación a la función modular.
        """
        if view.action in ["update", "partial_update"]:
            return self.check_update(request, view, obj)

        return True

    # ======================================================================
    #  🔥 FUNCIÓN: VALIDAR UPDATE / PATCH
    # ======================================================================
    def check_update(self, request, view, obj):
        """
        Reglas para modificar solicitudes como Supervisor:
        - Estado debe estar permitido
        - Solo modificar campos permitidos
        - No puede finalizar
        """

        # 1️⃣ Estado permitido
        if obj.estado not in EstadosSolicitud.SUPERVISOR_EDITABLES:
            raise PermissionDenied(
                f"No puedes modificar la solicitud porque el estado '{obj.estado}' "
                f"no está permitido para Supervisores."
            )

        # 2️⃣ Validar campos permitidos
        campos_enviados = set(request.data.keys())
        campos_invalidos = campos_enviados - self.CAMPOS_PERMITIDOS

        if campos_invalidos:
            raise PermissionDenied(
                f"Como Supervisor solo puedes modificar los campos: {self.CAMPOS_PERMITIDOS}"
            )
            

        # 3️⃣ No puede finalizar la solicitud
        if request.data.get("finalizado") is True:
            raise PermissionDenied("La solicitud ya fue finalizada y no puede modificarse.")
        
        # 5️⃣ El nuevo estado debe ser permitido
        nuevo_estado = request.data.get("estado")
        if nuevo_estado and nuevo_estado not in EstadosSolicitud.SUPERVISOR:
            raise PermissionDenied(
                f"No puedes usar el estado '{nuevo_estado}' para Supervisor Mesa de Partes."
            )

        return True
    
        
