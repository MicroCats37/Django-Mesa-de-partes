# permissions.py
from rest_framework.permissions import BasePermission

class IsExpedienteCreador(BasePermission):
    """
    Permite acciones solo si el usuario es el creador del expediente relacionado.
    """

    def has_object_permission(self, request, view, obj):
        # obj es un ExpedienteArchivoAnexo
        # Solo permite acciones si el usuario creó el expediente padre
        return obj.expediente.creado_por == request.user
