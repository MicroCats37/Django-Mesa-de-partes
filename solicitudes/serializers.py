from rest_framework import serializers
from usuarios.serializers import UsuarioSerializer
from expedientes.serializers import ExpedienteMiniSerializer
from .models import Expediente, Solicitud, ComentarioSolicitud,SolicitudArchivoAnexo,ComentarioSolicitudArchivoAnexo,UsuarioSolicitudAdjuntado
from django.contrib.auth.models import User


class SolicitudArchivoAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudArchivoAnexo
        fields = ["id", "solicitud", "archivo_anexo", "descripcion", "fecha_creacion"]
        read_only_fields = ["id", "fecha_creacion"]
        
# -----------------------------
# Comentario
# -----------------------------
       
class ComentarioSolicitudArchivoAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentarioSolicitudArchivoAnexo
        fields = [
            "id",
            "comentario",
            "archivo_anexo",
            "descripcion",
            "fecha_creacion",
        ]
        read_only_fields=["id","fecha_creacion"]
        
class ComentarioSolicitudSerializer(serializers.ModelSerializer):
    archivos_anexados = ComentarioSolicitudArchivoAnexoSerializer(
        many=True,
        read_only=True,
        source="comentario_solicitud"   # ← AQUÍ EL CAMBIO IMPORTANTE
    )
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = ComentarioSolicitud
        fields = ["id", "usuario", "solicitud","texto", "fecha_creacion", "archivos_anexados","parent"]
        read_only_fields = ["id", "usuario", "fecha_creacion"]
        
class UsuarioSolicitudAdjuntadoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True) 
    class Meta:
        model = UsuarioSolicitudAdjuntado
        fields = [
            "id",
            "usuario",
            "solicitud",
        ]
        
# --- Serializer de escritura (POST / PUT / PATCH) ---
class SolicitudWriteSerializer(serializers.ModelSerializer):
    expediente = serializers.PrimaryKeyRelatedField(
        queryset=Expediente.objects.all()
    )
    usuario_asignado = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    usuarios_adjuntados = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    # ------------------------------
    # CAMPOS VIRTUALES (FILES)
    # ------------------------------
    archivos_anexados = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    archivos_anexados_descripciones = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Solicitud
        fields = [
            "usuarios_adjuntados",
            "expediente",
            "usuario_asignado",
            "estado",
            "finalizado",
            "archivos_anexados",
            "archivos_anexados_descripciones",
        ]

    def validate(self, attrs):
        """
        Validaciones de negocio + coherencia de anexos
        """
        archivos = attrs.get("archivos_anexados", [])
        descripciones = attrs.get("archivos_anexados_descripciones", [])

        # Validar coherencia archivos / descripciones
        if archivos or descripciones:
            if len(archivos) != len(descripciones):
                raise serializers.ValidationError(
                    "La cantidad de archivos debe coincidir con la cantidad de descripciones."
                )

        instance = self.instance

        # Validar finalizar
        if instance and attrs.get("finalizado") is True:
            tiene_anexos = (
                bool(archivos) or
                instance.solicitud_archivo_anexo.exists()
            )

            if not tiene_anexos:
                raise serializers.ValidationError(
                    "No puedes finalizar una solicitud sin anexos."
                )

        return attrs

class SolicitudReadSerializer(serializers.ModelSerializer):
    
    usuarios_adjuntados = UsuarioSolicitudAdjuntadoSerializer(
        many=True,
        read_only=True,
        source="usuario_solicitud_adjuntado"   # <-- IMPORTANTE
    )
    evidencia_anexada = SolicitudArchivoAnexoSerializer(
        many=True,
        read_only=True,
        source="solicitud_archivo_anexo"   # <-- IMPORTANTE
    )
    comentarios = ComentarioSolicitudSerializer(
        many=True,
        read_only=True, # ← este es el related_name del modelo
        source="comentarios_solicitud" 
    )
    expediente = ExpedienteMiniSerializer(read_only=True)
    usuario_asignado = UsuarioSerializer(read_only=True)
    modificado_por = UsuarioSerializer(read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            "id",
            "expediente",
            "usuario_asignado",
            "modificado_por",
            "estado",
            "finalizado",
            "fecha_creacion",
            "fecha_actualizacion",
            "fecha_limite",
            "fecha_cierre",
            "evidencia_anexada",
            "usuarios_adjuntados",
            "comentarios",
        ]
        read_only_fields = fields

       
class ResumenSolicitudSerializer(serializers.ModelSerializer):
    # Accedemos a los datos del expediente a través de la relación OneToOne
    expediente_id_publico = serializers.CharField(source='expediente.id_publico')
    id_expediente = serializers.IntegerField(source='expediente.id')
    id_solicitud = serializers.IntegerField(source='id')

    class Meta:
        model = Solicitud
        fields = ['expediente_id_publico', 'id_solicitud', 'id_expediente']