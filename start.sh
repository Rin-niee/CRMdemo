#!/bin/bash

echo "🚀 Запуск CRM системы..."

# Создание директорий для статических и медиа файлов
mkdir -p static media

# Сборка и запуск контейнеров
echo "📦 Сборка Docker образов..."
docker-compose build

echo "🔧 Запуск сервисов..."
docker-compose up -d

echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса сервисов
echo "📊 Статус сервисов:"
docker-compose ps

echo "✅ CRM система запущена!"
echo "🌐 Веб-интерфейс доступен по адресу: http://localhost"
echo "🤖 Telegram бот запущен автоматически"
echo ""
echo "Для просмотра логов используйте:"
echo "  docker-compose logs -f web          # Логи Django"
echo "  docker-compose logs -f telegram_bot # Логи Telegram бота"
echo "  docker-compose logs -f nginx        # Логи Nginx"
echo ""
echo "Для остановки: docker-compose down"
