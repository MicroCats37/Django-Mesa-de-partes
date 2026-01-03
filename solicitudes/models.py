from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from expedientes.models import Expediente
from common.utils.constants.solicitudes.estados import EstadosSolicitud

from simple_history.models import HistoricalRecords


    
class Solicitud(models.Model):
    
    expediente = models.OneToOneField(
        Expediente,
        on_delete=models.PROTECT,
        related_name="solicitud"
    )
    usuario_asignado = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="solicitudes_asignadas"
    )
    modificado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="solicitud_modificada"
    )
    
    estado = models.CharField(max_length=20, choices=EstadosSolicitud.CHOICES, default="EN_GESTION_MP")
    finalizado = models.BooleanField(default=False)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.fecha_limite:
            self.fecha_limite = timezone.now() + timedelta(days=2)
            
        if self.estado == "REENVIO_MP":
            self.fecha_limite = None
        if self.finalizado and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()

        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.usuario_asignado.username}"

class SolicitudArchivoAnexo(models.Model):
    
    def solicitud_anexo_path(instance, filename):
        solicitud = instance.solicitud
        return f"solicitudes/{solicitud.id}/anexos/{filename}"
    
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="solicitud_archivo_anexo"
    )
    archivo_anexo = models.FileField(upload_to=solicitud_anexo_path)
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
class ComentarioSolicitud(models.Model):
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="comentarios_solicitud"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE  # ya no SET_NULL
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        related_name="respuestas",
        on_delete=models.CASCADE
    )
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.usuario.username}: {self.texto[:30]}"

class ComentarioSolicitudArchivoAnexo(models.Model):

    def comentario_anexo_path(instance, filename):
        comentario = instance.comentario
        solicitud = comentario.solicitud
        return f"solicitudes/{solicitud.id}/comentarios/{comentario.id}/{filename}"

    comentario = models.ForeignKey(
        ComentarioSolicitud,
        on_delete=models.CASCADE,
        related_name="comentario_solicitud"
    )
    archivo_anexo = models.FileField(upload_to=comentario_anexo_path)
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.descripcion}"
    
class UsuarioSolicitudAdjuntado(models.Model):
    solicitud = models.ForeignKey(
        Solicitud,
        on_delete=models.CASCADE,
        related_name="usuario_solicitud_adjuntado"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE  # ya no SET_NULL
    )
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.usuario.username}: {self.solicitud}"

