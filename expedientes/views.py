# views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Expediente ,ExpedienteArchivoAnexo
from .serializers import (
    ExpedienteSerializer, 
    ExpedienteArchivoAnexoSerializer
)
from rest_framework.exceptions import ValidationError
from common.utils.constants.expediente.ubigeo.datos import DEPARTAMENTOS, PROVINCIAS, DISTRITOS
from .permissions.django_permissions_coment import DjangoModelPermissionsConMensaje

from .permissions.rol.expediente_archivo_anexo.encargado_de_area import (
    EncargadoAreaExpedienteArchivoAnexoPermission,)
from .permissions.rol.expediente_archivo_anexo.recepcion_mesa_de_partes_permissions import (
    RecepcionMesaDePartesExpedienteArchivoAnexoPermission,
)
from .permissions.rol.expediente_archivo_anexo.supervisor_mesa_de_partes import (
    SupervisorMesaDePartesExpedienteArchivoAnexoPermission
)

from .permissions.rol.expediente.base import (MesaDePartesExpedientePermission)
 
# ================================================
# 📌 EXPEDIENTES
# ================================================
class ExpedienteViewSet(viewsets.ModelViewSet):
    queryset = Expediente.objects.all().order_by("-fecha_creacion")
    serializer_class = ExpedienteSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    permission_classes=[permissions.IsAuthenticated,DjangoModelPermissionsConMensaje,MesaDePartesExpedientePermission] #

    # 🔍 Búsqueda
    search_fields = ["id_publico", "dni", "apellidos", "nombres", "numero_documento"]

    # 🔧 Filtros
    filterset_fields = ["departamento", "provincia", "distrito"]

    # ↕ Ordenamiento
    ordering_fields = ["fecha_creacion", "id_publico"]
    ordering = ["-fecha_creacion"]

    # ----------------------------
    # Guardar expediente con anexos
    # ----------------------------
    # Guardar expediente con anexos
    def perform_create(self, serializer):
        dpto = serializer.validated_data.get("departamento")
        prov = serializer.validated_data.get("provincia")
        dist = serializer.validated_data.get("distrito")

        if dpto not in DEPARTAMENTOS:
            raise ValidationError("Departamento inválido")
        if prov not in PROVINCIAS[dpto]:
            raise ValidationError("Provincia no corresponde al departamento")
        if dist not in DISTRITOS[(dpto, prov)]:
            raise ValidationError("Distrito no corresponde a la provincia")

        expediente = serializer.save(creado_por=self.request.user)

        anexos = self.request.FILES.getlist("archivos_anexados")
        descripciones = self.request.data.getlist("archivos_anexados_descripciones")

        for archivo, descripcion in zip(anexos, descripciones):
            ExpedienteArchivoAnexo.objects.create(
                expediente=expediente,
                archivo_anexo=archivo,
                descripcion=descripcion
            )

    # Actualizar expediente
    def update(self, request, *args, **kwargs):
        expediente = self.get_object()
        serializer = self.get_serializer(expediente, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Anexos nuevos
        anexos = request.FILES.getlist("archivos_anexados")
        descripciones = request.data.getlist("archivos_anexados_descripciones")

        for archivo, descripcion in zip(anexos, descripciones):
            ExpedienteArchivoAnexo.objects.create(
                expediente=expediente,
                archivo_anexo=archivo,
                descripcion=descripcion
            )

        return Response(serializer.data)

    # ----------------------------
    # Filtros de usuario creador
    # ----------------------------
    
    def _paginar_queryset(self, queryset):
        """
        Helper para paginar cualquier queryset y devolver Response
        en el formato DRF paginado.
        """
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="creadas")
    def creadas(self, request):
        qs = Expediente.objects.filter(creado_por=request.user).order_by("-fecha_creacion")
        return self._paginar_queryset(qs)

    @action(detail=False, methods=["get"], url_path="creadas-sin-solicitud")
    def creadas_sin_solicitud(self, request):
        qs = Expediente.objects.filter(creado_por=request.user, solicitud__isnull=True).distinct().order_by("-fecha_creacion")
        return self._paginar_queryset(qs)
    
class ExpedienteArchivoAnexoViewSet(viewsets.ModelViewSet):
    queryset = ExpedienteArchivoAnexo.objects.all()
    serializer_class = ExpedienteArchivoAnexoSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_permissions(self):
        user = self.request.user

        if user.groups.filter(name="Recepcion Mesa de Partes").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                RecepcionMesaDePartesExpedienteArchivoAnexoPermission()
            ]
        if user.groups.filter(name="Supervisor Mesa de Partes").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                SupervisorMesaDePartesExpedienteArchivoAnexoPermission()
            ]
        if user.groups.filter(name="Encargado de Área").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                EncargadoAreaExpedienteArchivoAnexoPermission()
            ]

        # Default
        return [
            permissions.IsAuthenticated(),
            DjangoModelPermissionsConMensaje(),
        ] # 👈 Aquí asignas el permiso personalizado

    # Opcional: filtrar solo los anexos del usuario logueado
    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(expediente__creado_por=user)