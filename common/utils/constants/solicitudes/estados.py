from typing import List, Dict, Any, Tuple

RolInterno = str # Define el tipo de rol para claridad

class EstadosSolicitud:
    """
    Estado unificado para el flujo de solicitudes, con metadata de visibilidad y mutabilidad.
    """
    
    # =======================================================
    # MAPA BASE DE ESTADOS (ESTADOS_BASE)
    # =======================================================
    ESTADOS_BASE: Dict[str, Dict[str, Any]] = {
        # 1. ESTADO DE INICIO Y GESTIÓN INTERNA DE MESA DE PARTES (MP)
        "EN_GESTION_MP": {
            "label": "En Gestión (Mesa de Partes)",
            "roles": ["MESA_DE_PARTES"],
            "editable_by": ["MESA_DE_PARTES","SUPERVISOR"], # MP puede editar aquí
            "view_by": ["MESA_DE_PARTES"], 
            "description": "Solicitud creada y en proceso de revisión administrativa, asignación de área o corrección de datos por parte de Recepción."
        },
        
        # 2. ESTADOS DE TRANSICIÓN Y DEVOLUCIÓN ADMINISTRATIVA
        "REENVIO_MP": {
            "label": "Reenvío a Mesa de Partes",
            "roles": ["MESA_DE_PARTES", "SUPERVISOR", "AREA_ENCARGADA"],
            "editable_by": ["MESA_DE_PARTES"], # Solo MP debe editar para reencauzar
            "view_by": ["SUPERVISOR","AREA_ENCARGADA"],
            "description": "Devuelto a MP por error administrativo (área incorrecta, asignación), requiere que MP lo corrija y reenvíe."
        },
        "ENVIADO_A_AREA": {
            "label": "Enviado a Área Encargada",
            "roles": ["MESA_DE_PARTES", "SUPERVISOR", "AREA_ENCARGADA"],
            # MP o Supervisor pueden hacer una corrección de última hora/redirección antes de que el área inicie.
            "editable_by": ["SUPERVISOR","AREA_ENCARGADA"], 
            "view_by": ["SUPERVISOR","AREA_ENCARGADA"],
            "description": "Enviada a la Unidad de Ejecución para su gestión de fondo o validación."
        },
        
        # 3. ESTADOS DE GESTIÓN EN EL ÁREA ENCARGADA (Validación y Trámite)
        "EN_TRAMITE_AREA": {
            "label": "En Trámite (Área)",
            "roles": ["AREA_ENCARGADA"],
            "editable_by": ["AREA_ENCARGADA"], # Solo el Área Encargada edita el contenido del trámite
            "view_by": ["AREA_ENCARGADA"],
            "description": "El Área Encargada está procesando o revisando la solicitud para su resolución."
        },
        "CERRADO": {
            "label": "Cerrado",
            "roles": ["AREA_ENCARGADA"],
            "editable_by": ["AREA_ENCARGADA"], # Cerrado, contenido NO editable
            "view_by": ["AREA_ENCARGADA"],
            "description": "Proceso finalizado y archivado."
        },
    }

    # =======================================================
    # PROPIEDADES DE LISTAS PRECALCULADAS
    # La solución al NameError es usar list comprehensions directas
    # =======================================================
    
    # --- CHOICES para Django Models ---
    CHOICES: List[Tuple[str, str]] = [(key, value["label"]) for key, value in ESTADOS_BASE.items()]

    # --- Estados de Visibilidad/Propiedad ---
    MESA_DE_PARTES = [
        key for key, value in ESTADOS_BASE.items()
        if "MESA_DE_PARTES" in value["roles"]
    ]
    SUPERVISOR = [
        key for key, value in ESTADOS_BASE.items()
        if "SUPERVISOR" in value["roles"]
    ]
    AREA_ENCARGADA = [
        key for key, value in ESTADOS_BASE.items()
        if "AREA_ENCARGADA" in value["roles"]
    ]

    # --- Permisos de Mutación (LO QUE NECESITAS para .is_editable) ---
    MESA_DE_PARTES_EDITABLES = [
        key for key, value in ESTADOS_BASE.items()
        if "MESA_DE_PARTES" in value["editable_by"]
    ]
    SUPERVISOR_EDITABLES = [
        key for key, value in ESTADOS_BASE.items()
        if "SUPERVISOR" in value["editable_by"]
    ]
    AREA_ENCARGADA_EDITABLES = [
        key for key, value in ESTADOS_BASE.items()
        if "AREA_ENCARGADA" in value["editable_by"]
    ]

    # =======================================================
    # FUNCIONALIDAD ADICIONAL (Para validaciones más limpias)
    # =======================================================
    
    # Opción A: Función de verificación (robusta)
    @staticmethod
    def puede_editar_por(estado_actual: str, rol_usuario: RolInterno) -> bool:
        """
        Verifica si el rol del usuario tiene permiso para mutar la solicitud
        dado su estado, usando las listas precalculadas.
        """
        # Genera el nombre de la propiedad a consultar (e.g., 'AREA_ENCARGADA_EDITABLES')
        attr_name = f"{rol_usuario}_EDITABLES"
        
        # Obtiene la lista de estados editables o una lista vacía si el rol no tiene la propiedad
        editable_states = getattr(EstadosSolicitud, attr_name, [])
        
        return estado_actual in editable_states

    # =======================================================
    # MAPAS (Mantienen su funcionalidad)
    # =======================================================
    TODOS = list(ESTADOS_BASE.keys())
    MAPA_ESTADO = ESTADOS_BASE