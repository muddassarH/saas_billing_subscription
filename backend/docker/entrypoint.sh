#!/usr/bin/env sh
set -e

echo "Waiting for database..."
until python -c "import psycopg2, os; psycopg2.connect(host=os.getenv('POSTGRES_HOST','db'), port=os.getenv('POSTGRES_PORT','5432'), dbname=os.getenv('POSTGRES_DB','saas_billing'), user=os.getenv('POSTGRES_USER','postgres'), password=os.getenv('POSTGRES_PASSWORD','postgres'))" >/dev/null 2>&1; do
  sleep 1
done

if [ "${RUN_BOOTSTRAP_TASKS:-false}" = "true" ]; then
  echo "Applying migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput

  echo "Seeding plans..."
  python manage.py seed_plans || true
fi

exec "$@"
