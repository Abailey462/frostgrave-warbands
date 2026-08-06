#!/bin/sh
set -e

echo "Waiting for database at $DB_HOST:$DB_PORT..."
while ! python -c "
import socket, os, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ.get('DB_HOST','db'), int(os.environ.get('DB_PORT','5432'))))
    s.close()
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "Database is up."

python manage.py migrate --noinput
python manage.py seed_data
python manage.py collectstatic --noinput

if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

exec gunicorn frostgrave_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
