release: bash release.sh
web: gunicorn spotshot.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A spotshot worker -l info
beat: celery -A spotshot beat -l info
