from django.core.management.base import BaseCommand
from myapp.models import Currency

class Command(BaseCommand):
    help = 'Инициализация базовых валют в системе'

    def handle(self, *args, **options):
        # Базовые валюты для системы
        currencies = [
            {'code': 'RUB', 'name': 'Российский рубль', 'symbol': '₽'},
            {'code': 'USD', 'name': 'Доллар США', 'symbol': '$'},
            {'code': 'EUR', 'name': 'Евро', 'symbol': '€'},
            {'code': 'GBP', 'name': 'Британский фунт', 'symbol': '£'},
            {'code': 'JPY', 'name': 'Японская иена', 'symbol': '¥'},
        ]
        
        created_count = 0
        for currency_data in currencies:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults=currency_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создана валюта: {currency.code} ({currency.symbol})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Валюта уже существует: {currency.code} ({currency.symbol})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Инициализация завершена. Создано {created_count} новых валют.')
        )