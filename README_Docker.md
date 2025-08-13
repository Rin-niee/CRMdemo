# 🐳 CRM система в Docker

Этот проект содержит CRM систему, упакованную в Docker контейнеры с автоматическим запуском Telegram бота и Nginx.

## 🚀 Быстрый запуск

### Требования
- Docker
- Docker Compose

### Запуск
```bash
# Сделать скрипт исполняемым (Linux/Mac)
chmod +x start.sh

# Запустить систему
./start.sh
```

Или вручную:
```bash
docker-compose up -d
```

## 🏗️ Архитектура

### Сервисы
1. **web** - Django приложение (порт 8000)
2. **telegram_bot** - Telegram бот (автозапуск)
3. **nginx** - Веб-сервер (порт 80)

### Сети
- Все сервисы работают в одной сети `crm_network`
- Nginx проксирует запросы к Django
- Telegram бот работает независимо

## 📁 Структура файлов

```
├── Dockerfile              # Образ для Django и Telegram бота
├── docker-compose.yml      # Конфигурация сервисов
├── nginx.conf             # Конфигурация Nginx
├── requirements.txt       # Python зависимости
├── start.sh              # Скрипт запуска
└── .dockerignore         # Исключения для Docker
```

## 🔧 Управление

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f web
docker-compose logs -f telegram_bot
docker-compose logs -f nginx
```

### Остановка
```bash
docker-compose down
```

### Перезапуск
```bash
docker-compose restart
```

### Обновление
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Доступ

- **Веб-интерфейс**: http://localhost
- **API**: http://localhost/api/
- **Статические файлы**: http://localhost/static/
- **Медиа файлы**: http://localhost/media/

## 🤖 Telegram бот

- Автоматически запускается при старте системы
- Работает в отдельном контейнере
- Автоматически перезапускается при сбоях
- Логи доступны через `docker-compose logs -f telegram_bot`

## 📊 Мониторинг

### Статус сервисов
```bash
docker-compose ps
```

### Использование ресурсов
```bash
docker stats
```

## 🛠️ Разработка

### Локальная разработка
```bash
# Запуск только Django
docker-compose up web

# Запуск с пересборкой
docker-compose up --build
```

### Отладка
```bash
# Вход в контейнер
docker-compose exec web bash
docker-compose exec telegram_bot bash
docker-compose exec nginx sh
```

## 🔒 Безопасность

- Django работает от непривилегированного пользователя
- Nginx настроен с базовыми заголовками безопасности
- Контейнеры изолированы друг от друга

## 📝 Логи

Логи сохраняются в контейнерах и доступны через:
- `docker-compose logs`
- Внутри контейнеров в `/var/log/`

## 🚨 Устранение неполадок

### Проблемы с портами
```bash
# Проверить занятые порты
netstat -tulpn | grep :80
netstat -tulpn | grep :8000
```

### Проблемы с правами
```bash
# Исправить права на файлы
sudo chown -R $USER:$USER .
chmod +x start.sh
```

### Очистка Docker
```bash
# Удалить неиспользуемые образы
docker system prune -a

# Удалить все контейнеры и образы
docker system prune -a --volumes
```
