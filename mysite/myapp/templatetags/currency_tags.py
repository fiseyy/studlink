from django import template
from myapp.currency_service import CurrencyService

register = template.Library()

@register.filter
def format_currency(amount, currency_code):
    """Форматирование суммы с валютой"""
    service = CurrencyService()
    return service.format_currency(amount, currency_code)

@register.filter
def convert_to_currency(task, target_currency):
    """Конвертация стоимости задачи в указанную валюту"""
    service = CurrencyService()
    
    # Проверяем, является ли task объектом модели или Decimal
    if hasattr(task, 'cost'):
        # Это объект модели FreelanceTask
        cost_rub = service.get_task_cost_in_base_currency(task)
    else:
        # Это уже Decimal значение стоимости
        cost_rub = float(task)
    
    # Получаем целевую валюту
    try:
        from myapp.models import Currency
        target_curr = Currency.objects.get(code=target_currency)
        
        # Конвертируем из базовой валюты в целевую
        # cost_rub / target_curr.rate = стоимость в целевой валюте
        converted_amount = cost_rub / float(target_curr.rate)
        
        return service.format_currency(converted_amount, target_currency)
        
    except Currency.DoesNotExist:
        return f"{cost_rub:,} {target_currency}".replace(',', ' ')

@register.simple_tag
def get_currency_symbol(currency_code):
    """Получение символа валюты"""
    try:
        from myapp.models import Currency
        currency = Currency.objects.get(code=currency_code)
        return currency.symbol
    except Currency.DoesNotExist:
        return currency_code

@register.simple_tag
def get_currency_rate(currency_code):
    """Получение текущего курса валюты"""
    try:
        from myapp.models import Currency
        currency = Currency.objects.get(code=currency_code)
        # В реальной системе нужно получать курс из базы данных
        # Пока возвращаем заглушку
        return 1.0
    except Currency.DoesNotExist:
        return 1.0