from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from expedientes.models import Expediente, ExpedienteArchivoAnexo
from solicitudes.models import Solicitud, ComentarioSolicitud
from usuarios.models import PerfilUsuario, Area



class Command(BaseCommand):
    help = "Crea roles, usuarios, áreas y perfiles base con permisos estándar."

    def handle(self, *args, **kwargs):

        # -----------------------------
        # 1. CREAR GRUPOS (ROLES)
        # -----------------------------
        mesa_group, _ = Group.objects.get_or_create(name="Recepcion Mesa de Partes")
        encargado_group, _ = Group.objects.get_or_create(name="Encargado de Área")
        supervisor_group, _ = Group.objects.get_or_create(name="Supervisor Mesa de Partes")

        # -----------------------------
        # 2. CONTENT TYPES
        # -----------------------------
        ct_perfilusuario = ContentType.objects.get_for_model(PerfilUsuario) 
        ct_expediente = ContentType.objects.get_for_model(Expediente)
        ct_solicitud = ContentType.objects.get_for_model(Solicitud)
        ct_comentario = ContentType.objects.get_for_model(ComentarioSolicitud)
        ct_archivo = ContentType.objects.get_for_model(ExpedienteArchivoAnexo)

        # -----------------------------
        # 3. PERMISOS NATIVOS DJANGO
        # -----------------------------
        permisos_perfilusuario = {
            "view": Permission.objects.get(codename="view_perfilusuario", content_type=ct_perfilusuario),
        }
        
        permisos_expediente = {
            "view": Permission.objects.get(codename="view_expediente", content_type=ct_expediente),
            "add": Permission.objects.get(codename="add_expediente", content_type=ct_expediente),
            "change": Permission.objects.get(codename="change_expediente", content_type=ct_expediente),
        }

        permisos_solicitud = {
            "view": Permission.objects.get(codename="view_solicitud", content_type=ct_solicitud),
            "add": Permission.objects.get(codename="add_solicitud", content_type=ct_solicitud),
            "change": Permission.objects.get(codename="change_solicitud", content_type=ct_solicitud),
        }

        permisos_comentario = {
            "view": Permission.objects.get(codename="view_comentariosolicitud", content_type=ct_comentario),
            "add": Permission.objects.get(codename="add_comentariosolicitud", content_type=ct_comentario),
        }

        permisos_archivo = {
            "view": Permission.objects.get(codename="view_expedientearchivoanexo", content_type=ct_archivo),
            "add": Permission.objects.get(codename="add_expedientearchivoanexo", content_type=ct_archivo),
            "change": Permission.objects.get(codename="change_expedientearchivoanexo", content_type=ct_archivo),
            "delete": Permission.objects.get(codename="delete_expedientearchivoanexo", content_type=ct_archivo),
        }

        # -----------------------------
        # 4. ASIGNAR PERMISOS A GRUPOS
        # -----------------------------
        mesa_group.permissions.set([
            permisos_perfilusuario["view"],
            permisos_expediente["view"], permisos_expediente["add"], permisos_expediente["change"],
            permisos_solicitud["view"], permisos_solicitud["add"], permisos_solicitud["change"],
            permisos_comentario["view"], permisos_comentario["add"],
            permisos_archivo["view"], permisos_archivo["add"],permisos_archivo["change"], permisos_archivo["delete"],
        ])

        encargado_group.permissions.set([
            permisos_perfilusuario["view"],
            permisos_expediente["view"],
            permisos_solicitud["view"], permisos_solicitud["change"],
            permisos_comentario["view"], permisos_comentario["add"],
            permisos_archivo["view"],
        ])

        supervisor_group.permissions.set([
            permisos_perfilusuario["view"],
            permisos_expediente["view"],
            permisos_solicitud["view"], permisos_solicitud["change"],
            permisos_comentario["view"], permisos_comentario["add"],
            permisos_archivo["view"],
        ])

        # -----------------------------
        # 5. CREAR ÁREAS
        # -----------------------------
        nombres_areas = [
            "Atención al Colegiado", "Convenios", "Certificados", "Tecnología de la Información",
            "Contabilidad", "IEPI", "Tribunal de Ética", "Servicios Generales", "Seguridad",
            "Asesoría Legal", "Dirección de Tesorería", "Centro de Peritaje", "Centro Médico",
            "Caja", "Comisión de Asuntos Municipales", "Comité de Damas", "Comunicaciones",
            "Logística", "Vicedecanato", "Decanato", "Colegiación", "Dirección de Secretaría",
            "Centro de esparcimiento Ing. Jose Tong Matos", "Centro de Arbitraje - JRD",
            "Oficina de Comisiones", "CIDI Biblioteca", "Asistencia Social", "Recursos Humanos",
            "Sistema Integrado de Gestión", "Capitulo de Ingeniería Agrícola",
            "Capitulo de Ingeniería Económica y Administrativa", "Capitulo de Ingeniería Forestal",
            "Capitulo de Ingeniería Industrias Alimentarias", "Capitulo de Ingeniería de Minas",
            "Capitulo de Ingeniería Química", "Capitulo de Ingeniería Agronómica y Zootecnia",
            "Capitulo de Ingeniería Eléctrica", "Capitulo de Ingeniería Geológica",
            "Capitulo de Ingeniería Metalúrgia", "Capitulo de Ingeniería Pesquera",
            "Capitulo de Ingeniería Ambiental", "Capitulo de Ingeniería Geográfica",
            "Capitulo de Ingeniería Civil", "Capitulo de Ingeniería Electrónica",
            "Capitulo de Ingeniería Industrial, de Sistemas y Transporte",
            "Capitulo de Ingeniería Mecánica y Mecánica Eléctrica",
            "Capitulo de Ingeniería de Petróleo y Petroquímica",
            "Capitulo de Ingeniería Sanitaria e Higiene y Seguridad Industrial",
            "Comité Local Barranca Cajatambo", "Comité Local Cañete - Yauyos",
            "Comité Local Huaura Oyón"
        ]

        areas = {}
        for nombre in nombres_areas:
            area, _ = Area.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": f"Área {nombre}"}
            )
            areas[nombre] = area

        # -----------------------------
        # 6. CREAR / OBTENER RECEPCIÓN — SIN USAR EL DICCIONARIO
        # -----------------------------
        area_recepcion, _ = Area.objects.get_or_create(
            nombre="Recepción de Documentos",
            defaults={"descripcion": "Área de recepción y coordinación de documentos"}
        )

        # -----------------------------
        # 7. CREAR 1 USUARIO POR CADA ÁREA
        # -----------------------------
        def normalizar(texto):
            return (
                texto.lower()
                .replace("á", "a").replace("é", "e").replace("í", "i")
                .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
                .replace(" ", "_")
            )

        for area_nombre, area in areas.items():
            username = normalizar(area_nombre)
            user, created = User.objects.get_or_create(username=username)

            if created:
                user.first_name = area_nombre.split()[0]
                user.last_name = "Area"
                user.email = f"{username}@miempresa.com"
                user.set_password("123456")
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username}"))
            else:
                self.stdout.write(f"Usuario ya existe: {username}")

            user.groups.add(encargado_group)

            PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={"area": area, "cargo": "Encargado de Área"}
            )

        # -----------------------------
        # 8. Crear usuarios Mesa de Partes y Supervisores
        # -----------------------------
        usuarios_mesa = ["mesa1", "mesa2", "mesa3"]
        usuarios_super = ["supervisor"]

        for username in usuarios_mesa:
            u, created = User.objects.get_or_create(username=username)
            if created:
                u.set_password("123456")
                u.email = f"{username}@miempresa.com"
                u.first_name = username
                u.last_name = "Mesa"
                u.is_staff = True
                u.save()
            u.groups.add(mesa_group)
            PerfilUsuario.objects.get_or_create(
                user=u,
                defaults={"area": area_recepcion, "cargo": "Mesa de Partes"}
            )

        for username in usuarios_super:
            u, created = User.objects.get_or_create(username=username)
            if created:
                u.set_password("123456")
                u.email = f"{username}@cip.org"
                u.first_name = username
                u.last_name = "Supervisor"
                u.is_staff = True
                u.save()
            u.groups.add(supervisor_group)
            PerfilUsuario.objects.get_or_create(
                user=u,
                defaults={"area": area_recepcion, "cargo": "Supervisor"}
            )

        self.stdout.write(self.style.SUCCESS("TODO CREADO CORRECTAMENTE 🚀"))
