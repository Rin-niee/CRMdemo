# Sewa-motors-bot
Демо бот для CRM Sewa Motors

## Запуск проекта

1. Создайте виртуальное окружение:
    ```bash
    python3 -m venv myenv
    ```
3.  Активируйте виртуальное окружение:
    ```bash
    venv\Scripts\activate
    ```
    или
    ```bash
    source myenv/bin/activate
    ```
4.  Файлы `.env` и `db.sqlite3` уже есть в репозитории как временное решение, их можно не создвать
5.  Установите зависимости
    ```bash
    pip install -r requirements.txt
    ```
6.  Запустите бота
   ```bash
   python main.py
   ```
7. Для того чтобы назначить администратора измените ADMIN_ID в .env и перезапустите бота