from rest_framework.permissions import BasePermission

class ICanChangePermission(BasePermission):
    """
    Controla que puedes modificar
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Superuser → siempre puede
        if user.is_superuser:
            return True

        # SOLO aplica en update/partial_update
        if view.action not in ["update", "partial_update"]:
            return True

        # Mesa de Partes → no puede modificar
        if user.groups.filter(name="Mesa de Partes").exists():
            return False

        # Supervisor Mesa de Partes → solo si está asignada a él
        if user.groups.filter(name="Supervisor Mesa de Partes").exists():
            return obj.usuario_asignado == user

        # Encargado de Área → solo si está asignada a él
        if user.groups.filter(name="Encargado de Área").exists():
            return obj.usuario_asignado == user

        # Usuario normal → solo si está asignada a él
        return obj.usuario_asignado == user
