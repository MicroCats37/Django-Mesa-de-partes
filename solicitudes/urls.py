from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedDefaultRouter # (Si no lo usas, puedes quitarlo)
from django.urls import path, include
from .views import (
    SolicitudViewSet, 
    ComentarioSolicitudViewSet, 
)

router = DefaultRouter()

router.register(r"solicitudes", SolicitudViewSet, basename="solicitudes")
router.register(r"comentarios-solicitud", ComentarioSolicitudViewSet, basename="comentarios-solicitud")

# --- ERROR ANTERIOR ---
# router.register(r"pendientes", MisSolicitudesView.as_view(), basename="pendientes")  <-- ESTO ESTABA MAL

urlpatterns = [
    path("", include(router.urls)),
]