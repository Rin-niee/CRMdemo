FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=CRMdemo.settings

COPY . .

CMD sh -c "python manage.py collectstatic --noinput --clear && gunicorn --bind 0.0.0.0:8000 CRMdemo.wsgi:application"

