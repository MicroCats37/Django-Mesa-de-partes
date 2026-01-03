from rest_framework.routers import DefaultRouter
# from rest_framework_nested.routers import NestedDefaultRouter # (Si no lo usas, puedes quitarlo)
from django.urls import path, include
from .views import (
    ExpedienteViewSet, 
)

router = DefaultRouter()
router.register(r"expedientes", ExpedienteViewSet)

# --- ERROR ANTERIOR ---
# router.register(r"pendientes", MisSolicitudesView.as_view(), basename="pendientes")  <-- ESTO ESTABA MAL

urlpatterns = [
    path("", include(router.urls)),
]