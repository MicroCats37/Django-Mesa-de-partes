from rest_framework.permissions import BasePermission

# ----------------------------------
# Solo ver anexos de expedientes
# ----------------------------------
class SupervisorMesaDePartesViewExpedienteArchivoAnexoPermission(BasePermission):
    """
    Permite que Supervisores y Encargados de Área solo vean anexos de expedientes.
    Ninguna acción de escritura (create/update/delete) está permitida.
    """
    def has_permission(self, request, view):
        # Permite únicamente métodos de solo lectura
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Permite ver siempre los objetos
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        # Bloquea cualquier otra acción
        return False


# ----------------------------------
# Parent permission
# ----------------------------------
class SupervisorMesaDePartesExpedienteArchivoAnexoPermission(BasePermission):
    """
    Combina permisos del Supervisor Mesa de Partes
    """
    def has_permission(self, request, view):
        return SupervisorMesaDePartesViewExpedienteArchivoAnexoPermission().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return SupervisorMesaDePartesViewExpedienteArchivoAnexoPermission().has_object_permission(request, view, obj)
