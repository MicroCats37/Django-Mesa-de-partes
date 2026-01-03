from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedDefaultRouter # (Si no lo usas, puedes quitarlo)
from django.urls import path, include
from .views import (
    ExpedienteViewSet, 
    SolicitudViewSet, 
    ComentarioSolicitudViewSet, 
    MeView, 
    PerfilUsuarioViewSet, 
    AreaViewSet, 
    MisSolicitudesView, 
    LoginView
)

router = DefaultRouter()
router.register(r"expedientes", ExpedienteViewSet)
router.register(r"solicitudes", SolicitudViewSet, basename="solicitudes")
router.register(r"perfil-usuario", PerfilUsuarioViewSet, basename="perfil-usuario")
router.register(r"area", AreaViewSet, basename="area")
router.register(r"comentarios-solicitud", ComentarioSolicitudViewSet, basename="comentarios-solicitud")

# --- ERROR ANTERIOR ---
# router.register(r"pendientes", MisSolicitudesView.as_view(), basename="pendientes")  <-- ESTO ESTABA MAL

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path('me/', MeView.as_view(), name='me'),
    path("pendientes/", MisSolicitudesView.as_view(), name="pendientes"),

    path("", include(router.urls)),
]