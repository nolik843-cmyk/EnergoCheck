# EnergoCheck

Веб-приложение для автоматизации учета электроэнергии, договоров, расчетов, оплат и аналитики для энергоснабжающей организации.

## Стек

- Python 3.13+
- Django 6.1
- PostgreSQL 15/16
- Bootstrap 5.3
- htmx 2.0
- pytest + pytest-django
- Ruff

## Быстрый старт

1. Создайте виртуальное окружение.
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Скопируйте переменные окружения:
   ```bash
   copy .env.example .env
   ```
4. Проверьте настройки подключения в `.env`:
   ```env
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=0000
   DB_HOST=localhost
   DB_PORT=5432
   ```
5. Запустите проект:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Структура проекта

Проект организован по доменным блокам: учет пользователей, потребители, биллинг, оплаты, уведомления и аналитика.
