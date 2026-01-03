# -------------------------------------------------------------------------
# ETAPA 1: BUILDER (Construcción)
# Se utiliza para instalar dependencias y compilar archivos (si es necesario)
# -------------------------------------------------------------------------
FROM python:3.10-slim as builder

# Define el directorio de trabajo
WORKDIR /app

# Configura variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# -------------------------------------------------------------------------
# ETAPA 2: PRODUCTION (Imagen Final)
# Una imagen mínima para correr la aplicación, copiando solo lo esencial.
# -------------------------------------------------------------------------
FROM python:3.10-slim

# Crea un usuario no-root para mayor seguridad y establece permisos
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

# Copia las librerías instaladas desde la etapa 'builder'
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Establece el directorio de trabajo y copia el código de la aplicación
WORKDIR /app
COPY --chown=appuser:appuser . .

# Cambia al usuario no-root
USER appuser

# Expone el puerto que usará Gunicorn
EXPOSE 5001

# Comando para iniciar la aplicación (Asume que tu proyecto se llama 'app')
CMD ["/app/docker-entrypoint.sh"]