#!/bin/sh
set -e

# ----------------------
# Variables de entorno necesarias para Django
# ----------------------
export PYTHONPATH=/app
export DJANGO_SETTINGS_MODULE=app.settings # Asegúrate de que 'app' sea el nombre de tu módulo base

# ----------------------
# Migraciones
# ----------------------
echo "[ENTRYPOINT] Aplicando migraciones..."
python manage.py migrate

# ----------------------
# Crear superusuario por defecto si no existe
# ----------------------
echo "[ENTRYPOINT] Verificando superusuario..."
echo "from django.contrib.auth import get_user_model; \
User = get_user_model(); \
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@example.com','admin')" | python manage.py shell


echo "[ENTRYPOINT] Creando Usuario"
python manage.py script_user_rol || echo "⚠️ no se pudieron crear por que existen"
# ----------------------
# 🚀 Iniciar servidor Gunicorn (PRODUCCIÓN) 🚀
# ----------------------
echo "[ENTRYPOINT] Iniciando servidor Gunicorn..."
# Reemplaza 'app.wsgi:application' si el nombre de tu módulo WSGI es diferente.
# '-w 4' define 4 workers, que es un buen punto de partida (2 * número_de_núcleos + 1).
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 4