FROM python:3.12-slim

# Устанавливаем зависимости для PostgreSQL + netcat
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменные окружения Django
ENV DJANGO_SETTINGS_MODULE=CRMdemo.settings

# Копируем весь проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput

# По умолчанию запускаем Gunicorn для веба
CMD ["gunicorn", "CRMdemo.wsgi:application", "--bind", "0.0.0.0:8000"]
