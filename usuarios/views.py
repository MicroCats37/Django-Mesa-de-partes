# views.py
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


from .serializers import (
    LoginSerializer, MeSerializer,AreaSerializer,
)

from .permissions.django_permissions_coment import DjangoModelPermissionsConMensaje

from rest_framework_simplejwt.views import TokenObtainPairView

from solicitudes.models import Solicitud
from solicitudes.serializers import ResumenSolicitudSerializer

from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer

class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PerfilUsuario.area.field.related_model.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissionsConMensaje,
    ]

    filterset_fields = ["nombre"]   # 👈 Esto te faltaba

    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre"]
    ordering = ["nombre"]

class PerfilUsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        DjangoModelPermissionsConMensaje,
    ]

    search_fields = ["user__username", "cargo"]

    # 🔧 Filtros
    filterset_fields = {
        "user": ["exact"],
        "area": ["exact"],                         # Filtrar por ID (ya lo tienes)
        "area__nombre": ["exact", "icontains"],    # 👈 FILTRAR POR NOMBRE DEL ÁREA
        "cargo": ["exact", "icontains"],
        "jefe": ["exact"],
    }

    ordering_fields = ["user__username", "cargo", "area"]
    ordering = ["user__username"]
    
    # =====================================================================
    # ENDPOINT: /perfil-usuario/mis-subordinados/
    # =====================================================================
    @action(detail=False, methods=["get"], url_path="mis-subordinados")
    def mis_subordinados(self, request):
        perfil = getattr(request.user, "perfilusuario", None)
        if not perfil:
            return self.paginated_response(PerfilUsuario.objects.none())
        qs = PerfilUsuario.objects.filter(jefe=perfil)
        return self.paginated_response(qs)

# ================================================
# LOGIN JWT
# ================================================
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


# ================================================
# PERFIL DEL USUARIO
# ================================================
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not hasattr(user, "perfilusuario"):
            return Response(
                {"detail": "El usuario no tiene un perfil asociado."},
                status=400
            )

        serializer = MeSerializer(user)
        return Response(serializer.data)
# ================================================

class MisSolicitudesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # --- 1. SOLICITUDES ADJUNTADAS (PENDIENTES) ---
        # Filtramos por usuario colaborador Y que NO estén finalizadas
        qs_adjuntadas = Solicitud.objects.filter(
            usuario_solicitud_adjuntado__usuario=user,
            finalizado=False  # <--- FILTRO AGREGADO
        ).distinct()
        
        data_adjuntadas = ResumenSolicitudSerializer(qs_adjuntadas, many=True).data

        # --- 2. SOLICITUDES ASIGNADAS (PENDIENTES) ---
        # Filtramos por usuario asignado Y que NO estén finalizadas
        qs_asignadas = Solicitud.objects.filter(
            usuario_asignado=user,
            finalizado=False  # <--- FILTRO AGREGADO
        )
        
        data_asignadas = ResumenSolicitudSerializer(qs_asignadas, many=True).data
        
        # --- RESPUESTA ---
        response_data = {
            "solicitudes_adjuntadas": {
                "cantidad": qs_adjuntadas.count(),
                "detalle": data_adjuntadas
            },
            "solicitud_asignado": {
                "cantidad": qs_asignadas.count(),
                "detalle": data_asignadas
            }
        }
        
        return Response(response_data)