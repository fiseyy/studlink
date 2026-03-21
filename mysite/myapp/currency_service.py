import requests
from datetime import date
from django.conf import settings
from .models import Currency, FreelanceTask

class CurrencyService:
    """Сервис для работы с курсами валют"""
    
    def __init__(self):
        # Базовая валюта для пересчета (например RUB)
        self.base_currency = getattr(settings, 'BASE_CURRENCY', 'RUB')
    
    def get_cbr_rates(self):
        """Получение курсов ЦБ РФ"""
        try:
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            rates = {}
            # Добавляем рубль как базовую валюту
            rates[self.base_currency] = 1.0
            
            for code, currency_data in data['Valute'].items():
                if currency_data['Nominal'] > 0:
                    rates[code] = currency_data['Value'] / currency_data['Nominal']
            
            return rates, data['Date'][:10]  # YYYY-MM-DD
        except Exception as e:
            print(f"Ошибка получения курсов: {e}")
            return None, None
    
    def update_currency_rates(self):
        """Обновление курсов валют в базе данных"""
        rates, rate_date = self.get_cbr_rates()
        if not rates:
            return False
        
        # Обновляем курсы для всех валют
        for currency in Currency.objects.all():
            if currency.code in rates:
                currency_rate = rates[currency.code]
                
                # Обновляем все задачи в этой валюте
                FreelanceTask.objects.filter(
                    currency=currency,
                    currency_rate_date__lt=rate_date
                ).update(
                    currency_rate=currency_rate,
                    currency_rate_date=rate_date
                )
        
        return True
    
    def get_task_cost_in_base_currency(self, task):
        """Получение стоимости задачи в базовой валюте"""
        return task.cost * task.currency_rate
    
    def format_currency(self, amount, currency_code):
        """Форматирование суммы с валютой"""
        try:
            currency = Currency.objects.get(code=currency_code)
            return f"{amount:,} {currency.symbol}".replace(',', ' ')
        except Currency.DoesNotExist:
            return f"{amount:,} {currency_code}".replace(',', ' ')