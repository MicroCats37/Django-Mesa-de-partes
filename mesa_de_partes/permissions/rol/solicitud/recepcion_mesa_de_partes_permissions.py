from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from ....constants.solicitudes.estados import EstadosSolicitud


class RecepcionMesaDePartesSolicitudPermission(BasePermission):
    """
    Permisos modulares para Mesa de Partes:

    Cada acción tiene su propia función:
    - check_create()
    - check_update()
    
    Esto permite agregar fácilmente:
    - check_assign()
    - check_finalize()
    - check_approve()
    - etc.
    """

    CAMPOS_PERMITIDOS = {"estado", "usuario_asignado","usuarios_adjuntados"}

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE VISTA
    # ----------------------------------------------------------------------
    def has_permission(self, request, view):
        """Redirige a la función adecuada según la acción."""
        action = view.action

        if action == "create":
            return self.check_create(request, view)

        if action == "destroy":
            return False
        return True

    # ----------------------------------------------------------------------
    # PERMISOS A NIVEL DE OBJETO (update, patch)
    # ----------------------------------------------------------------------
    def has_object_permission(self, request, view, obj):
        """Redirige según la acción."""
        action = view.action

        if action in ["update", "partial_update"]:
            return self.check_update(request, view, obj)

        return True

    # ======================================================================
    #  🔥 FUNCIÓN: VALIDAR CREACIÓN
    # ======================================================================
    def check_create(self, request, view):
        """
        Mesa de Partes puede crear solicitudes:
        - Debe seleccionar expediente
        - No puede marcar finalizado
        - Estado debe ser permitido
        - No puede asignarse a sí mismo
        - No asignar a alguien de su mismo área
        """

        # 1️⃣ Validar expediente
        expediente_id = request.data.get("expediente")
        if not expediente_id:
            raise PermissionDenied("Debes seleccionar un expediente.")

        # 2️⃣ No permitir finalizado
        finalizado = request.data.get("finalizado")
        if finalizado not in [None, False, "false", "False", 0, "0"]:
            raise PermissionDenied(
                "No puedes marcar una solicitud como finalizada al crearla."
            )

        # 3️⃣ Estado permitido
        estado = request.data.get("estado")
        if estado not in EstadosSolicitud.MESA_DE_PARTES_EDITABLES:
            raise PermissionDenied(
                f"No puedes usar el estado '{estado}' al crear la solicitud."
            )

        # 4️⃣ Asignación
        user = request.user
        asignado_id = request.data.get("usuario_asignado")

        # No asignarse a sí mismo
        if str(asignado_id) == str(user.id):
            raise PermissionDenied("No puedes asignarte la solicitud a ti mismo.")

        # No asignar a misma área
        self._validate_area_assignment(user, asignado_id)

        return True

    # ======================================================================
    #  🔥 FUNCIÓN: VALIDAR UPDATE / PATCH
    # ======================================================================
    def check_update(self, request, view, obj):
        """
        Reglas para modificar solicitud:
        - Debe haber creado el expediente
        - No modificar si finalizada
        - Solo campos permitidos
        - No puede finalizar
        - Estado debe ser permitido
        """

        user = request.user

        # 1️⃣ Solo puede modificar lo que él creó
        if obj.expediente.creado_por != user:
            raise PermissionDenied(
                "Solo puedes modificar solicitudes cuyo expediente tú has creado."
            )

        # 2️⃣ No puede modificar si finalizada
        if obj.finalizado:
            raise PermissionDenied("La solicitud ya está finalizada.")

        # 2️⃣.1️⃣ 🔥 NUEVA VALIDACIÓN (ESTADO ACTUAL)
        if obj.estado not in EstadosSolicitud.MESA_DE_PARTES_EDITABLES:
            raise PermissionDenied(
                f"No puedes modificar la solicitud cuando está en estado '{obj.estado}'."
            )
        # 3️⃣ Campos permitidos
        campos_enviados = set(request.data.keys())
        campos_invalidos = campos_enviados - self.CAMPOS_PERMITIDOS

        if campos_invalidos:
            raise PermissionDenied(
                f"Solo puedes modificar los campos: {', '.join(self.CAMPOS_PERMITIDOS)}"
            )

        # 4️⃣ No puede finalizar
        if request.data.get("finalizado") in [True, "true", "True", 1, "1"]:
            raise PermissionDenied("No puedes finalizar una solicitud desde Mesa de Partes.")

        # 5️⃣ El nuevo estado debe ser permitido
        nuevo_estado = request.data.get("estado")
        if nuevo_estado and nuevo_estado not in EstadosSolicitud.MESA_DE_PARTES:
            raise PermissionDenied(
                f"No puedes usar el estado '{nuevo_estado}' para Mesa de Partes."
            )

        return True

    # ======================================================================
    #  🔧 FUNCIÓN AUXILIAR: VALIDAR ÁREA DE ASIGNACIÓN
    # ======================================================================
    def _validate_area_assignment(self, user, asignado_id):
        """No asignar a misma área y validar existencia del usuario asignado."""
        perfil = getattr(user, "perfilusuario", None)

        if not perfil or not perfil.area:
            return True

        User = get_user_model()

        try:
            asignado_user = User.objects.get(id=asignado_id)
        except User.DoesNotExist:
            raise PermissionDenied("El usuario asignado no existe.")

        asignado_perfil = getattr(asignado_user, "perfilusuario", None)

        if asignado_perfil and asignado_perfil.area == perfil.area:
            raise PermissionDenied(
                "No puedes asignar la solicitud a alguien de tu misma área."
            )

        return True
