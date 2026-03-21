from celery import shared_task
from .currency_service import CurrencyService

@shared_task
def update_currency_rates_task():
    """Celery задача для автоматического обновления курсов валют"""
    service = CurrencyService()
    success = service.update_currency_rates()
    
    if success:
        print("Курсы валют успешно обновлены")
    else:
        print("Ошибка при обновлении курсов валют")
    
    return success

@shared_task
def update_currency_rates_daily():
    """Ежедневное обновление курсов валют"""
    return update_currency_rates_task.delay()