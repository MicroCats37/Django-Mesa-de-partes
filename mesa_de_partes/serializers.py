from rest_framework import serializers
from .models import Expediente, Solicitud, ComentarioSolicitud, ExpedienteArchivoAnexo,SolicitudArchivoAnexo,ComentarioSolicitudArchivoAnexo,UsuarioSolicitudAdjuntado
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from .models import PerfilUsuario
from .constants.expediente.ubigeo.datos import DEPARTAMENTOS, PROVINCIAS, DISTRITOS

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name","email"]

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario.area.field.related_model
        fields = ["id", "nombre", "descripcion"]

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    user = UsuarioSerializer(read_only=True) 
    area = AreaSerializer(read_only=True)
    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "user",
            "area",
            "cargo",
            "jefe",
        ]


# -----------------------------
# Expediente
# -----------------------------



class ExpedienteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediente
        fields = [  
                "id", 
                "id_publico", 
                "tipo_documento",
                "dni",
                "apellidos",
                "nombres",
                "telefono",
                "correo",
                "departamento",
                "provincia",
                "distrito",
                ]

class SolicitudMiniSerializer(serializers.ModelSerializer):
    usuario_asignado = UsuarioSerializer(read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            "id",
            "estado",
            "usuario_asignado",
            "finalizado",
            "fecha_creacion",
            "fecha_limite",
            "fecha_cierre",
        ]

class ExpedienteArchivoAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpedienteArchivoAnexo
        fields = ["id", "archivo_anexo", "descripcion", "fecha_creacion"]



class ExpedienteSerializer(serializers.ModelSerializer):
    creado_por = UsuarioSerializer(read_only=True)
    archivos_anexados = ExpedienteArchivoAnexoSerializer(many=True,required=False)
    solicitud = SolicitudMiniSerializer(read_only=True)
    class Meta:
        model = Expediente
        fields = [
            "id",
            "id_publico",

            "tipo_persona",
            "dni",
            "ruc",
            "razon_social",
            "apellidos",
            "nombres",
            "telefono",
            "correo",

            "departamento",
            "provincia",
            "distrito",

            "tipo_documento",
            "numero_documento",
            "numero_folios",
            "asunto",
            
            "archivo_principal",
            "archivos_anexados",
            "solicitud",
            "creado_por",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

        read_only_fields = [
            "id",
            "id_publico",
            "creado_por",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        
    def validate(self, data):

        #Validacion de UBIGEO
        dpto = data.get("departamento")
        prov = data.get("provincia")
        dist = data.get("distrito")

        # 1. Validar departamento
        if dpto not in DEPARTAMENTOS:
            raise serializers.ValidationError({
                "departamento": "El departamento no es válido."
            })

        # 2. Validar provincia
        if prov not in PROVINCIAS[dpto]:
            raise serializers.ValidationError({
                "provincia": f"La provincia no pertenece a {dpto}."
            })

        # 3. Validar distrito
        if dist not in DISTRITOS[(dpto, prov)]:
            raise serializers.ValidationError({
                "distrito": f"El distrito no pertenece a {prov}."
            })

        return data



# -----------------------------
# Solicitud
# -----------------------------





class SolicitudArchivoAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudArchivoAnexo
        fields = ["id", "solicitud", "archivo_anexo", "descripcion", "fecha_creacion"]
        read_only_fields = ["id", "fecha_creacion"]
        
# -----------------------------
# Comentario
# -----------------------------

#solicitud puedes adjuntar archivos si eres el area encargado

        
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

       
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        perfil = getattr(user, "perfilusuario", None)
        if perfil is None:
            raise ValidationError("El usuario no tiene perfil asociado. Contacte al administrador.")

        # Obtener el rol del usuario
        rol = user.groups.first()
        if rol is None:
            raise ValidationError("El usuario no tiene un rol asignado. Contacte al administrador.")

        token = super().get_token(user)

        token["user_id"] = user.id
        token["username"] = user.username
        token["fullname"] = f"{user.first_name} {user.last_name}".strip()
        token["email"] = user.email
        token["rol"] = rol.name
        token["cargo"] = perfil.cargo
        token["area"] = perfil.area.nombre if perfil.area else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        perfil = getattr(user, "perfilusuario", None)

        # Perfil obligatorio
        if perfil is None:
            raise ValidationError("El usuario no tiene un perfil asignado. No puede iniciar sesión.")

        # Rol obligatorio
        rol = user.groups.first()
        if rol is None:
            raise ValidationError("El usuario no tiene un rol asignado. No puede iniciar sesión.")

        data["user"] = {
            "user_id": user.id,
            "username": user.username,
            "fullname": f"{user.first_name} {user.last_name}".strip(),
            "email":user.email,
            "rol": rol.name,
            "cargo" : perfil.cargo,
            "area" : perfil.area.nombre if perfil.area else None
        }
        

        return data

class MeSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    rol = serializers.SerializerMethodField()
    perfil = serializers.SerializerMethodField()
    permisos = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "fullname",
            "email",
            "rol",
            "perfil",
            "permisos",
        ]

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_rol(self, obj):
        grupo = obj.groups.first()
        return grupo.name if grupo else None

    def get_perfil(self, obj):
        perfil = getattr(obj, "perfilusuario", None)
        if not perfil:
            return None
        return {
            "id": perfil.id,
            "cargo": perfil.cargo,
            "area": perfil.area.nombre if perfil.area else None,
        }

    def get_permisos(self, obj):
        return list(obj.get_all_permissions())
    
class ResumenSolicitudSerializer(serializers.ModelSerializer):
    # Accedemos a los datos del expediente a través de la relación OneToOne
    expediente_id_publico = serializers.CharField(source='expediente.id_publico')
    id_expediente = serializers.IntegerField(source='expediente.id')
    id_solicitud = serializers.IntegerField(source='id')

    class Meta:
        model = Solicitud
        fields = ['expediente_id_publico', 'id_solicitud', 'id_expediente']