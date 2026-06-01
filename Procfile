release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn medicart.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
