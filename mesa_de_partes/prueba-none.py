
from django.contrib import admin
from .models import Expediente, Asignacion, PerfilUsuario, Area



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

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
# -----------------------------------------------------
# ADMIN DE EXPEDIENTE (solo expediente)
# -----------------------------------------------------

@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):

    list_display = ("id_publico", "nombre_expediente")
    search_fields = ("id_publico", "nombre_expediente")

    readonly_fields = ("id_publico", "fecha_creacion", "fecha_limite", "creado_por")

    def get_fields(self, request, obj=None):
        if obj:
            # Vista de detalle → mostrar todo, pero muchos son solo lectura
            return (
                "id_publico",
                "nombre_expediente",
                "fecha_creacion",
                "fecha_limite",
                "creado_por",
            )
        else:
            # Vista de creación → solo el nombre
            return ("nombre_expediente",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("id_publico", "fecha_creacion", "fecha_limite", "creado_por")
        return ()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return True  # puede ver, pero solo filtrado

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        # Solo deja cambiar si él lo creó
        if obj is not None and obj.creado_por == request.user:
            return True
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creado_por=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)



# -----------------------------------------------------
# ADMIN DE ASIGNACIÓN (separado totalmente)
# -----------------------------------------------------

@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):

    list_display = ("expediente", "usuario_asignado", "estado", "fecha_actualizacion")
    search_fields = (
        "expediente__id_publico",
        "usuario_asignado__user__username",
    )
    list_filter = ("estado", "usuario_asignado__area")

    readonly_fields = ("fecha_asignacion", "fecha_actualizacion") # <-- Mantener esto aquí o en get_readonly_fields

    # ---------------------------------------------------------------------
    # 5. CONTROLAR LOS CAMPOS VISIBLES EN EL FORMULARIO
    # ---------------------------------------------------------------------
    def get_fields(self, request, obj=None):
        
        # Campos de Asignación
        campos_base = (
            "expediente",
            "usuario_asignado",
            "estado",
            "comentario",
            "fecha_resolucion",
        )
        
        # Campos de solo lectura que deben mostrarse
        campos_solo_lectura = (
            "fecha_asignacion",
            "fecha_actualizacion",
            "modificado_por",
        )
        
        if obj:
            # Vista de Detalle/Edición
            # Se muestran todos los campos principales + los de solo lectura.
            return campos_base + campos_solo_lectura
        else:
            # Vista de Creación (Registro Nuevo)
            # Solo se necesitan los campos para crear la asignación inicial.
            return (
                "expediente",
                "usuario_asignado",
                "estado",
                "comentario",
            )
            

    def get_readonly_fields(self, request, obj=None):
        # La lógica es que la mayoría de los campos deben ser editables al CREAR,
        # pero inmutables o de solo lectura después de GUARDAR.
        
        # Campos que siempre deben ser de solo lectura (definidos en la clase)
        base_readonly = ("fecha_asignacion", "fecha_actualizacion")

        if obj:
            # Vista de Detalle/Edición: 
            # El Expediente y quién lo asignó inicialmente NO deben poder cambiarse.
            return base_readonly + (
                "expediente", 
                "modificado_por", 
                # Si quieres que el usuario_asignado SÓLO se cambie en el primer guardado, añádelo:
                # "usuario_asignado", 
            )
        else:
            # Vista de Creación: 
            # Solo los campos de fecha/registro interno son de solo lectura.
            return base_readonly + ("modificado_por",)

    # ---------------------------------------------------------------------
    # 1. FILTRAR LOS CAMPOS FOREIGN KEY (expediente, usuario_asignado)
    # ---------------------------------------------------------------------
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        grupos = request.user.groups.values_list("name", flat=True)
        perfil = PerfilUsuario.objects.filter(user=request.user).first()

        # -------- FILTRAR EXPEDIENTE SEGÚN EL ROL --------
        if db_field.name == "expediente" and not request.user.is_superuser:

            # Mesa → solo expedientes creados por el usuario
            if "Mesa" in grupos:
                kwargs["queryset"] = Expediente.objects.filter(creado_por=request.user)

            # Analista → expedientes asignados a él
            elif "Analista" in grupos:
                kwargs["queryset"] = Expediente.objects.filter(
                    asignacion__usuario_asignado__user=request.user
                ).distinct()

            # Supervisor → expedientes dentro de su área
            elif "Supervisor" in grupos:
                if perfil and perfil.area:
                    kwargs["queryset"] = Expediente.objects.filter(
                        asignacion__usuario_asignado__area=perfil.area
                    ).distinct()
                else:
                    kwargs["queryset"] = Expediente.objects.none()

        # ---------------------------------------------------------------------
        # -------- FILTRAR USUARIOS_ASIGNADO SEGÚN EL ROL (CORREGIDO) --------
        # ---------------------------------------------------------------------
        if db_field.name == "usuario_asignado" and not request.user.is_superuser:

            # 1. MESA: Ve a todos los usuarios que SÍ tienen un área asignada.
            if "Mesa" in grupos:
                kwargs["queryset"] = PerfilUsuario.objects.filter(area__isnull=False)
            
            # 2. OTROS ROLES (Analista/Supervisor): Ven solo a usuarios de su misma área.
            elif perfil and perfil.area:
                kwargs["queryset"] = PerfilUsuario.objects.filter(area=perfil.area)
            
            # 3. SEGURIDAD: Si no tiene un rol especial ni área, la lista está vacía.
            else:
                kwargs["queryset"] = PerfilUsuario.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # ---------------------------------------------------------------------
    # 2. FILTRAR ESTADOS SEGÚN EL ROL DEL USUARIO
    # ---------------------------------------------------------------------
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        
        if db_field.name == "estado" and not request.user.is_superuser:

            grupos = request.user.groups.values_list("name", flat=True)

            # MESA
            if "Mesa" in grupos:
                kwargs["choices"] = [
                    ("PENDIENTE", "Pendiente (Mesa de Partes)"),
                    ("AREA_EQUIVOCADA", "Área equivocada"),
                    ("ENVIADO_ANALISTA", "Enviado al Analista"),
                ]

            # ANALISTA
            elif "Analista" in grupos:
                kwargs["choices"] = [
                    ("EN_REVISION", "En revisión (Analista)"),
                    ("OBSERVADO", "Observado"),
                    ("AREA_EQUIVOCADA", "Área equivocada"),
                    ("ENVIADO_SUPERVISOR", "Enviado al Supervisor"),
                ]

            # SUPERVISOR
            elif "Supervisor" in grupos:
                kwargs["choices"] = [
                    ("APROBADO", "Aprobado"),
                    ("RECHAZADO", "Rechazado"),
                    ("CERRADO", "Cerrado"),
                ]

        return super().formfield_for_choice_field(db_field, request, **kwargs)

    # ---------------------------------------------------------------------
    # 3. FILTRAR QUÉ ASIGNACIONES PUEDE VER EN LA LISTA
    # ---------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs

        grupos = request.user.groups.values_list("name", flat=True)
        perfil = PerfilUsuario.objects.filter(user=request.user).first()

        # Mesa → ve solo asignaciones de expedientes que él creó
        if "Mesa" in grupos:
            return qs.filter(expediente__creado_por=request.user)

        # Analista → ve asignaciones dirigidas a él
        if "Analista" in grupos:
            return qs.filter(usuario_asignado__user=request.user)

        # Supervisor → ve asignaciones de su área
        if "Supervisor" in grupos:
            if perfil and perfil.area:
                return qs.filter(usuario_asignado__area=perfil.area)
            return qs.none()

        return qs

    # ---------------------------------------------------------------------
    # 4. GUARDAR QUIÉN MODIFICÓ LA ASIGNACIÓN
    # ---------------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
# FIN DEL ADMIN



'''
class PermisoSolicitud(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="permisos_solicitudes")
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name="permisos_usuario")
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    class Meta:
        unique_together = ("usuario", "solicitud", "permiso")
        verbose_name = "Permiso de Solicitud"
        verbose_name_plural = "Permisos de Solicitudes"

    def esta_activo(self):
        """Indica si el permiso sigue vigente."""
        if self.expiracion:
            return timezone.now() <= self.expiracion
        return True

    def __str__(self):
        return f"{self.usuario.username} → {self.permiso.nombre} ({self.solicitud})"
'''