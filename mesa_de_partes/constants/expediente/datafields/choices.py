TIPO_PERSONA_CHOICES = [
        ("NATURAL", "Persona Natural"),
        ("JURIDICA", "Persona Jurídica"),
    ]
    
TIPO_DOCUMENTO_CHOICES = (
    # Los valores en la base de datos se suelen poner en mayúsculas y sin acentos
    # para estandarización y evitar problemas, aunque no es estrictamente obligatorio.
    ('ACTA_SESION_ORDINARIA', 'Acta de Sesión Ordinaria'),
    ('CARTA', 'Carta'),
    ('CARTA_MULTIPLE', 'Carta Múltiple'),
    ('CARTA_NOTARIAL', 'Carta Notarial'),
    ('CEDULA_NOTIFICACION', 'Cédula de Notificación'),
    ('DISPOSICION_FISCAL', 'Disposición Fiscal'),
    ('FACTURA', 'Factura'),
    ('INFORME_VALORACION', 'Informe de Valoración'),
    ('INFORME_PERICIAL_PARTE', 'Informe Pericial de Parte'),
    ('OFICIO', 'Oficio'),
    ('OFICIO_CIRCULAR', 'Oficio Circular'),
    ('OFICIO_MULTIPLE', 'Oficio Múltiple'),
    ('OPINION', 'Opinión'),
    ('SOLICITUD', 'Solicitud'),
)