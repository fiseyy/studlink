from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('employer', 'Работодатель'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    university = models.CharField(max_length=100, blank=True)

    class Meta:
        swappable = 'AUTH_USER_MODEL'

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # Код валюты по ISO 4217 (USD, EUR, RUB)
    name = models.CharField(max_length=50)  # Полное название валюты (Доллар США, Евро, Российский рубль)
    symbol = models.CharField(max_length=5)  # Символ валюты ($, €, ₽)

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class FreelanceTask(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    executor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='executed_tasks')

    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()

    # Валютная система
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)  # Валюта задачи (USD, EUR, RUB)
    cost = models.DecimalField(max_digits=12, decimal_places=2)  # Стоимость в указанной валюте

    # Курс валюты для пересчета в базовую валюту
    currency_rate_date = models.DateField(null=True, blank=True)  # Дата последнего обновления курса
    currency_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.0)  # Коэффициент пересчета (1 USD = 90 RUB)
