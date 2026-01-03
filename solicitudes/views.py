# views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import  Solicitud, ComentarioSolicitud, SolicitudArchivoAnexo,ComentarioSolicitudArchivoAnexo,UsuarioSolicitudAdjuntado
from .serializers import (
    
    ComentarioSolicitudSerializer,
    SolicitudReadSerializer,SolicitudWriteSerializer
)
from rest_framework.exceptions import ValidationError
from .permissions.django_permissions_coment import DjangoModelPermissionsConMensaje
from .permissions.rol.solicitud.encargado_de_area import (
    EncargadoAreaSolicitudPermission,)
from .permissions.rol.solicitud.recepcion_mesa_de_partes_permissions import (
    RecepcionMesaDePartesSolicitudPermission,
)
from .permissions.rol.solicitud.supervisor_mesa_de_partes import (
    SupervisorMesaDePartesSolicitudPermission,
)
from .permissions.rol.comentario_solicitud.general_permission import (ComentarioSolicitudPermission)
from django.db import transaction

class SolicitudViewSet(viewsets.ModelViewSet):
    queryset = Solicitud.objects.all().order_by("-fecha_creacion")
    # 🔍 Búsqueda
    search_fields = ["expediente__id_publico"]

    # 🔧 Filtros
    filterset_fields = ["estado", "finalizado"]

    # ↕ Ordenamiento
    ordering_fields = ["fecha_creacion"]
    ordering = ["-fecha_creacion"]

    def get_permissions(self):
        user = self.request.user

        if user.groups.filter(name="Recepcion Mesa de Partes").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                RecepcionMesaDePartesSolicitudPermission()
            ]
        if user.groups.filter(name="Supervisor Mesa de Partes").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                SupervisorMesaDePartesSolicitudPermission()
            ]
        if user.groups.filter(name="Encargado de Área").exists():
            return [
                permissions.IsAuthenticated(),
                DjangoModelPermissionsConMensaje(),
                EncargadoAreaSolicitudPermission()
            ]

        return [
            permissions.IsAuthenticated(),
            DjangoModelPermissionsConMensaje(),
        ]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "asignadas", "creadas", "mi_area","adjuntadas"]:
            return SolicitudReadSerializer
        return SolicitudWriteSerializer

    # --------------------------------------------------------------------
    # CREAR SOLICITUD (SIN ANEXOS)
    # --------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = SolicitudWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        usuarios_adjuntados = data.pop("usuarios_adjuntados", [])

        solicitud = serializer.save(
            modificado_por=request.user
        )

        for uid in usuarios_adjuntados:
            UsuarioSolicitudAdjuntado.objects.get_or_create(
                solicitud=solicitud,
                usuario_id=uid
            )

        # 🔥 RESPUESTA CON SERIALIZER DE LECTURA
        read_serializer = SolicitudReadSerializer(
            solicitud,
            context={"request": request}
        )

        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
        )


    # --------------------------------------------------------------------
    # ACTUALIZAR SOLICITUD (AQUÍ SÍ SE AÑADEN ANEXOS)
    # --------------------------------------------------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        solicitud = self.get_object()
        
        serializer = self.get_serializer(
            solicitud,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        solicitud = serializer.save(
            modificado_por=self.request.user
        )
        # ------------------------------------------
        # Validación: NO permitir finalizar sin anexos
        # ------------------------------------------
        finalizado_flag = serializer.validated_data.get("finalizado")

        if finalizado_flag is True:
            if not solicitud.solicitud_archivo_anexo.exists():
                raise ValidationError(
                    "No puedes finalizar una solicitud sin anexos."
                )

        # Guardar actualización base
        self.perform_update(serializer)

        # ------------------------------------
        # USUARIOS ADJUNTADOS
        # ------------------------------------
        usuarios_adjuntados = serializer.validated_data.get(
            "usuarios_adjuntados", []
        )

        for uid in usuarios_adjuntados:
            UsuarioSolicitudAdjuntado.objects.get_or_create(
                solicitud=solicitud,
                usuario_id=uid
            )

        # ------------------------------------------
        # ANEXOS (YA VALIDADOS POR EL SERIALIZER)
        # ------------------------------------------
        archivos = serializer.validated_data.get(
            "archivos_anexados", []
        )
        descripciones = serializer.validated_data.get(
            "archivos_anexados_descripciones", []
        )

        for archivo, descripcion in zip(archivos, descripciones):
            SolicitudArchivoAnexo.objects.create(
                solicitud=solicitud,
                archivo_anexo=archivo,
                descripcion=descripcion
            )

        return Response(
            SolicitudReadSerializer(solicitud).data
        )

    # --------------------------------------------------------------------
    # HELPERS Y ACTIONS (SIN CAMBIOS)
    # --------------------------------------------------------------------
    def _paginar_queryset(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="asignadas")
    def asignadas(self, request):
        qs = Solicitud.objects.filter(usuario_asignado=request.user)
        return self._paginar_queryset(qs)

    @action(detail=False, methods=["get"], url_path="creadas")
    def creadas(self, request):
        qs = Solicitud.objects.filter(expediente__creado_por=request.user)
        return self._paginar_queryset(qs)

    @action(detail=False, methods=["get"], url_path="mi-area")
    def mi_area(self, request):
        perfil = getattr(request.user, "perfilusuario", None)
        
        # Validamos que el usuario tenga perfil y área asignada
        if not perfil or not perfil.area:
            return Response([], status=status.HTTP_200_OK)
        
        # Filtramos solicitudes donde el usuario asignado pertenece a la misma área
        qs = Solicitud.objects.filter(
            usuario_asignado__perfilusuario__area=perfil.area
        )
        
        return self._paginar_queryset(qs)
    
    @action(detail=False, methods=["get"], url_path="adjuntadas")
    def adjuntadas(self, request):
        """
        Retorna las solicitudes donde el usuario actual está en la lista de 'usuarios_adjuntados'.
        """
        # Usamos el related_name del modelo intermedio 'UsuarioSolicitudAdjuntado'
        # que definimos en los modelos como 'usuario_solicitud_adjuntado'
        qs = Solicitud.objects.filter(
            usuario_solicitud_adjuntado__usuario=request.user
        ).distinct() # distinct() es vital para evitar duplicados en relaciones Many-to-Many
        
        return self._paginar_queryset(qs)
            
# 📌 COMENTARIOS
# ================================================
class ComentarioSolicitudViewSet(viewsets.ModelViewSet):
    """
    - Crear comentarios de solicitudes
    - Adjuntar archivos en la misma creación (igual que expediente)
    - Listar, eliminar, actualizar comentarios
    """

    queryset = ComentarioSolicitud.objects.all().order_by("-fecha_creacion")
    serializer_class = ComentarioSolicitudSerializer
    # Importante mantener los parsers para manejar multipart/form-data
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated,ComentarioSolicitudPermission]

    # --------------------------------------------------------------------
    # CREAR COMENTARIO (CON ARCHIVOS)
    # --------------------------------------------------------------------
    @transaction.atomic
    def perform_create(self, serializer):
        request = self.request
        print(request.data)
        solicitud_id = request.data.get("solicitud")
        if not solicitud_id:
            raise ValidationError("Debe especificar un ID de solicitud.")

        # Validar que la solicitud exista
        try:
            solicitud = Solicitud.objects.get(id=solicitud_id)
        except Solicitud.DoesNotExist:
            raise ValidationError("La solicitud no existe.")

        # Crear comentario
        comentario = serializer.save(
            solicitud=solicitud,
            usuario=request.user
        )

        # ---------------------------
        # Manejo de anexos
        # ---------------------------
        anexos = request.FILES.getlist("archivos_anexados")
        
        # ✅ CORRECCIÓN: Usar request.POST.getlist() para campos de formulario
        descripciones = request.POST.getlist("archivos_anexados_descripciones") 

        for archivo, descripcion in zip(anexos, descripciones):
            ComentarioSolicitudArchivoAnexo.objects.create(
                comentario=comentario,
                archivo_anexo=archivo,
                descripcion=descripcion
            )

    # --------------------------------------------------------------------
    # ACTUALIZAR COMENTARIO (PERMITIR AGREGAR MÁS ARCHIVOS)
    # --------------------------------------------------------------------
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        comentario = self.get_object()
        
        # Validar que solo el autor pueda modificarlo
        if comentario.usuario != request.user:
            raise ValidationError("Solo el autor puede modificar su comentario.")

        serializer = self.get_serializer(
            comentario,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Agregar anexos nuevos
        anexos = request.FILES.getlist("archivos_anexados")
        
        # ✅ CORRECCIÓN: Usar request.POST.getlist() para campos de formulario
        descripciones = request.POST.getlist("archivos_anexados_descripciones")

        for archivo, descripcion in zip(anexos, descripciones):
            ComentarioSolicitudArchivoAnexo.objects.create(
                comentario=comentario,
                usuario=request.user,
                archivo_anexo=archivo,
                descripcion=descripcion
            )

        return Response(ComentarioSolicitudSerializer(comentario).data)

    # --------------------------------------------------------------------
    # LISTAR COMENTARIOS DE UNA SOLICITUD POR ID
    # --------------------------------------------------------------------
    def list(self, request, *args, **kwargs):
        solicitud_id = request.query_params.get("solicitud_id")

        if solicitud_id:
            qs = ComentarioSolicitud.objects.filter(
                solicitud_id=solicitud_id
            ).order_by("-fecha_creacion")
        else:
            qs = self.get_queryset()

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
