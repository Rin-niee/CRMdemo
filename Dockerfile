FROM python:3.12-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Gunicorn для Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "CRMdemo.wsgi:application"]