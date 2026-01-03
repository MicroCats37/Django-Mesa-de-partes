from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
import secrets
from .constants.solicitudes.estados import EstadosSolicitud
from .constants.expediente.ubigeo.datos import DEPARTAMENTOS, PROVINCIAS, DISTRITOS, DEPARTAMENTO_CHOICES, PROVINCIA_CHOICES, DISTRITO_CHOICES
from .constants.expediente.datafields.choices import TIPO_PERSONA_CHOICES, TIPO_DOCUMENTO_CHOICES
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords




class Permiso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
    
    

class Area(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
    
    


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.CharField(max_length=120, blank=True)
    jefe = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinados"
    )
    def clean(self):
        if self.jefe == self:
            raise ValidationError("No puedes ser tu propio jefe.")
    def __str__(self):
        return f"{self.user.username} - {self.cargo} ({self.area})"
    
    
    

class Expediente(models.Model):
    
    def expediente_principal_path(instance, filename):
        # Usa id_publico para que exista incluso antes de guardarse por primera vez
        return f"expedientes/{instance.id_publico}/principal/{filename}"
    
    id_publico = models.CharField(max_length=20, unique=True, editable=False)
    tipo_persona = models.CharField(max_length=20, choices=TIPO_PERSONA_CHOICES)
    dni = models.CharField(max_length=20)
    ruc = models.CharField(max_length=20, null=True,blank=True)
    razon_social = models.CharField(max_length=200, null=True,blank=True)
    apellidos = models.CharField(max_length=150)
    nombres = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30)
    correo = models.EmailField()
    
    departamento = models.CharField(max_length=120, choices=DEPARTAMENTO_CHOICES)
    provincia = models.CharField(max_length=120, choices=PROVINCIA_CHOICES)
    distrito = models.CharField(max_length=120, choices=DISTRITO_CHOICES)

    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(max_length=100)
    numero_folios = models.PositiveIntegerField()
    asunto = models.CharField(max_length=300)

    archivo_principal = models.FileField(upload_to=expediente_principal_path)
    
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="expedientes_creados")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    
    
    # ----------------------------
    # VALIDACIONES
    # ----------------------------
    def clean(self):
    # ===============================
    # VALIDAR DNI / RUC SEGÚN TIPO
    # ===============================
        if self.tipo_persona == "NATURAL":
            self.ruc = None
            self.razon_social = None
            # DNI obligatorio
            if not self.dni:
                raise ValidationError({"dni": "El DNI es obligatorio para personas naturales."})

            if not self.dni.isdigit():
                raise ValidationError({"dni": "El DNI debe contener solo números."})

            if len(self.dni) != 8:
                raise ValidationError({"dni": "El DNI debe tener exactamente 8 dígitos."})

        elif self.tipo_persona == "JURIDICA":
            self.dni = None
            # RUC obligatorio
            if not self.ruc:
                raise ValidationError({"ruc": "El RUC es obligatorio para personas jurídicas."})

            if not self.ruc.isdigit():
                raise ValidationError({"ruc": "El RUC debe contener solo números."})

            if len(self.ruc) != 11:
                raise ValidationError({"ruc": "El RUC debe tener exactamente 11 dígitos."})

            # Razón social obligatoria
            if not self.razon_social:
                raise ValidationError({"razon_social": "La razón social es obligatoria para personas jurídicas."})

        # ===============================
        # VALIDAR TELÉFONO
        # ===============================
        if not self.telefono.isdigit():
            raise ValidationError({"telefono": "El teléfono debe contener solo números."})

        if len(self.telefono) < 7 or len(self.telefono) > 9:
            raise ValidationError({"telefono": "El teléfono debe tener entre 7 y 9 dígitos."})

        # ===============================
        # VALIDAR UBIGEO
        # ===============================
        dpto = self.departamento
        prov = self.provincia
        dist = self.distrito

        if dpto not in DEPARTAMENTOS:
            raise ValidationError({"departamento": "El departamento no es válido."})

        if prov not in PROVINCIAS.get(dpto, []):
            raise ValidationError({"provincia": f"La provincia no pertenece a {dpto}."})

        if dist not in DISTRITOS.get((dpto, prov), []):
            raise ValidationError({"distrito": f"El distrito no pertenece a {prov}."})

        # ===============================
        # VALIDAR Nº DE DOCUMENTO
        # ===============================
        if len(self.numero_documento) < 3:
            raise ValidationError({"numero_documento": "El número de documento debe tener al menos 3 caracteres."})

    # SAVE
    # ----------------------------
    def save(self, *args, **kwargs):

        if not self.id_publico:
            fecha = timezone.now().strftime("%Y%m%d")
            aleatorio = secrets.token_hex(4).upper()
            self.id_publico = f"LIMA-{fecha}-{aleatorio}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_publico}"
    
class ExpedienteArchivoAnexo(models.Model):
    
    def expediente_anexo_path(instance, filename):
        expediente = instance.expediente
        return f"expedientes/{expediente.id_publico}/anexos/{filename}"
    
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="archivos_anexados"
    )
    archivo_anexo = models.FileField(upload_to=expediente_anexo_path)
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ejecuta validaciones
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.archivo_anexo.name}"

    
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

