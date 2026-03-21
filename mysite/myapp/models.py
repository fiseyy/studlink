from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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

    interactions = GenericRelation(Interaction, related_query_name='freelance_tasks')

class Vacancy(models.Model):
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs' )
    hired_candidate = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hired_jobs')
    
    title = models.CharField(max_lenght=80)
    description = models.TextField()
    expiration = models.DateTimeField()

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)

    salary_from = models.DecimalField(max_digits=12, decimal_places=2)
    salary_to = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    currency_rate_date = models.DateField(null=True, blank=True)  # Дата последнего обновления курса
    currency_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.0)  # Коэффициент пересчета (1 USD = 90 RUB)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    interactions = GenericRelation(Interaction, related_query_name='vacancies')

class Interaction(models.Model):
    INTERACTION_TYPE = [
        ('view', 'View'),
        ('apply', 'Apply'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPE)

    created_at = models.DateTimeField(auto_now_add=True)