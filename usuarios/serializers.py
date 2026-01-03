from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from .models import PerfilUsuario

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
    