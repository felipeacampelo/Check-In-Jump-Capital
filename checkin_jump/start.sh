#!/bin/bash

echo "Starting Check-in JUMP application..."

# Verificar se as variáveis de ambiente estão configuradas
if [ -z "$PORT" ]; then
    echo "Warning: PORT environment variable not set, using default 8000"
    export PORT=8000
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    exit 1
fi

# Navegar para o diretório correto (se necessário)
if [ -d "checkin_jump" ]; then
    echo "Navigating to checkin_jump directory..."
    cd checkin_jump
fi

# Executar migrações se necessário
echo "Running database migrations..."
python manage.py migrate --noinput

# Coletar arquivos estáticos se necessário
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Iniciar o servidor
echo "Starting Gunicorn server on port $PORT..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info 