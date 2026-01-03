from rest_framework import serializers
from .models import Expediente, ExpedienteArchivoAnexo
from usuarios.serializers import UsuarioSerializer
from common.utils.constants.expediente.ubigeo.datos import DEPARTAMENTOS, PROVINCIAS, DISTRITOS
from solicitudes.models import Solicitud


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






        

        

