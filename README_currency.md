# Автоматическое получение курсов валют

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка Redis (для Celery)

Установите Redis и запустите сервер:

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
redis-server

# Windows
# Скачайте Redis для Windows и запустите redis-server.exe
```

## Инициализация валют

```bash
python manage.py init_currencies
```

## Запуск Celery

```bash
# В одном терминале запустите воркер Celery
celery -A mysite worker -l info

# В другом терминале запустите планировщик Celery
celery -A mysite beat -l info
```

## Ручное обновление курсов

```python
from myapp.currency_service import CurrencyService

service = CurrencyService()
service.update_currency_rates()
```

## Использование в коде

```python
from myapp.currency_service import CurrencyService
from myapp.models import FreelanceTask

# Получение стоимости в базовой валюте
task = FreelanceTask.objects.get(id=1)
service = CurrencyService()
cost_rub = service.get_task_cost_in_base_currency(task)

# Форматирование суммы
formatted = service.format_currency(1000.50, 'USD')  # "1 000,50 $"
```

## API ЦБ РФ

Сервис использует официальный API ЦБ РФ: https://www.cbr-xml-daily.ru/

Курсы обновляются ежедневно в 11:30 по московскому времени.