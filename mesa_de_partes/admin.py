from django.contrib import admin
from .models import Expediente,PerfilUsuario, Area,ExpedienteArchivoAnexo
from django.utils import timezone

from django.core.exceptions import PermissionDenied

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "area", "cargo", "jefe")
    search_fields = ("user__username", "cargo")
    list_filter = ("area",)

    # Para que el campo jefe solo muestre perfiles existentes
    autocomplete_fields = ["jefe", "user", "area"]

    fieldsets = (
        ("Información del usuario", {
            "fields": ("user",)
        }),
        ("Organización", {
            "fields": ("area", "cargo", "jefe")
        }),
    )
    
from django.contrib import admin
from .models import Expediente, Solicitud

# --------------------------------------------------------
# Inline de Solicitud para mostrar dentro de Expediente
# --------------------------------------------------------

# ==========================
#   INLINE DE ARCHIVOS
# ==========================



# ==========================
#      ADMIN EXPEDIENTE
# ==========================

from django import forms

class ExpedienteAdminForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        tipo_persona = cleaned_data.get("tipo_persona")
        ruc = cleaned_data.get("ruc")
        razon_social = cleaned_data.get("razon_social")

        # Validación condicional para persona jurídica
        if tipo_persona == "JURIDICA":
            if not ruc:
                self.add_error("ruc", "El RUC es obligatorio para personas jurídicas.")
            if not razon_social:
                self.add_error("razon_social", "La razón social es obligatoria para personas jurídicas.")
                
        return cleaned_data

class ExpedienteArchivoAnexoInline(admin.TabularInline):
    model = ExpedienteArchivoAnexo
    extra = 0
    readonly_fields = ("fecha_creacion",)
    
# ==============================
# ADMIN DE EXPEDIENTE
# ==============================
@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    form = ExpedienteAdminForm
    inlines = [ExpedienteArchivoAnexoInline]  # Solo anexos

    list_display = (
        "id_publico", "tipo_persona", "dni", "apellidos", "nombres",
        "ruc", "razon_social",
        "numero_documento", "creado_por", "fecha_creacion", "archivo_principal"
    )

    readonly_fields = ("id_publico", "fecha_creacion", "fecha_actualizacion")

    # -----------------------------
    # FILTRAR SOLO EXPEDIENTES DEL USUARIO
    # -----------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creado_por=request.user)

    # -----------------------------
    # CONTROLAR PERMISOS DE EDICIÓN
    # -----------------------------
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True  # listado permitido
        solicitud = getattr(obj, "solicitud", None)
        if solicitud is None:
            return True  # permite editar si no hay solicitud
        return solicitud.estado == "EN_GESTION_MP"

    # -----------------------------
    # GUARDAR MODELO
    # -----------------------------
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        else:
            solicitud = getattr(obj, "solicitud", None)
            if solicitud and solicitud.estado != "EN_GESTION_MP":
                raise PermissionDenied("Solo puedes editar expedientes cuya solicitud está en estado PENDIENTE.")
        super().save_model(request, obj, form, change)
        
        
from django.contrib.auth.models import User


# --------------------------------------------------------
# Admin de Solicitud
# --------------------------------------------------------
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "expediente",
        "usuario_asignado",
        "modificado_por",
        "estado",
        "finalizado",
        "fecha_cierre",
        "fecha_actualizacion",
        "fecha_cierre",
    )

    readonly_fields = (
        "fecha_cierre",
        "fecha_actualizacion",
        "fecha_cierre",
    )

    # -----------------------------
    # FILTRAR A QUIÉN PUEDO ASIGNAR
    # -----------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = request.user

        # SUPERUSER → sin restricciones
        if user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # Obtener perfil
        try:
            perfil = user.perfilusuario
        except PerfilUsuario.DoesNotExist:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # -------------------------------------------------------
        # FILTRAR CAMPO expediente (solo ve los que él creó)
        # -------------------------------------------------------
        if db_field.name == "expediente":
            kwargs["queryset"] = Expediente.objects.filter(creado_por=user)
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # -------------------------------------------------------
        # FILTRAR CAMPO usuario_asignado
        # -------------------------------------------------------
        if db_field.name == "usuario_asignado":

            # A) Cualquier usuario del área “Mesa de Partes” → SOLO SU JEFE
            if perfil.area and perfil.area.nombre == "Mesa de Partes":
                if perfil.jefe:
                    kwargs["queryset"] = User.objects.filter(id=perfil.jefe.user.id)
                else:
                    kwargs["queryset"] = User.objects.none()
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

            # B) Supervisores Mesa de Partes → NO pueden asignar a Mesa de Partes
            if user.groups.filter(name="Supervisor Mesa de Partes").exists():
                usuarios_mesa = PerfilUsuario.objects.filter(
                    area__nombre="Mesa de Partes"
                ).values_list("user_id", flat=True)

                kwargs["queryset"] = User.objects.exclude(id__in=usuarios_mesa)
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

            # C) Encargado de Área → SOLO SU JEFE
            if user.groups.filter(name="Encargado de Área").exists():
                if perfil.jefe:
                    kwargs["queryset"] = User.objects.filter(id=perfil.jefe.user.id)
                else:
                    kwargs["queryset"] = User.objects.none()
                return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # -------------------------------------------------------
        # modificado_por siempre es el usuario actual
        # -------------------------------------------------------
        if db_field.name == "modificado_por":
            kwargs["queryset"] = User.objects.filter(id=user.id)
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # -----------------------------
    # CAMPOS READONLY SEGÚN ROL
    # -----------------------------
    def get_readonly_fields(self, request, obj=None):
        user = request.user

        fields = list(self.readonly_fields)

        if not user.is_superuser:
            # Recepción Mesa → no puede cerrar la solicitud
            if user.groups.filter(name="Recepcion Mesa de Partes").exists():
                fields.append("finalizado")

            # Encargado de Área → fecha de cierre no editable
            if user.groups.filter(name="Encargado de Área").exists():
                fields.append("fecha_cierre")

        return fields

    # ---------------------------------
    # SAVE → fecha_cierre automática
    # ---------------------------------
    def save_model(self, request, obj, form, change):
        obj.modificado_por = request.user

        # Si finaliza, registrar fecha de cierre
        if obj.finalizado and obj.fecha_cierre is None:
            obj.fecha_cierre = timezone.now()

        super().save_model(request, obj, form, change)