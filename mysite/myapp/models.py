from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


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
    rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.0)  # Текущий курс к базовой валюте
    rate_date = models.DateField(null=True, blank=True)  # Дата последнего обновления курса

    def __str__(self):
        return f"{self.code} ({self.symbol})"

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
    
    title = models.CharField(max_length=80)
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


class ChatRoom(models.Model):
    """Комнаты для общения"""
    ROOM_TYPE_CHOICES = [
        ('direct', 'Прямой чат'),
        ('task', 'Чат по задаче'),
        ('vacancy', 'Чат по вакансии'),
        ('group', 'Групповой чат'),
    ]
    
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='direct')
    
    # Для прямых чатов
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    
    # Для чатов по задачам и вакансиям
    task = models.ForeignKey(FreelanceTask, on_delete=models.CASCADE, null=True, blank=True)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, null=True, blank=True)
    
    # Для групповых чатов
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.room_type == 'direct':
            users = self.participants.all()
            if users.count() == 2:
                return f"Чат между {users[0].username} и {users[1].username}"
            return f"Прямой чат ({users.count()} участников)"
        elif self.room_type == 'task':
            return f"Чат по задаче: {self.task.title}"
        elif self.room_type == 'vacancy':
            return f"Чат по вакансии: {self.vacancy.title}"
        return self.name or f"Чат {self.id}"


class Message(models.Model):
    """Сообщения в чатах"""
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Текст'),
        ('file', 'Файл'),
        ('image', 'Изображение'),
        ('system', 'Системное сообщение'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    
    # Для файлов и изображений
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)
    
    # Цитирование сообщений
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."
    
    def mark_as_read(self, user):
        """Отметить сообщение как прочитанное пользователем"""
        self.read_by.add(user)
        self.is_read = self.read_by.count() > 0
        self.save()


class Notification(models.Model):
    """Уведомления о новых сообщениях"""
    NOTIFICATION_TYPE_CHOICES = [
        ('new_message', 'Новое сообщение'),
        ('message_read', 'Сообщение прочитано'),
        ('chat_invitation', 'Приглашение в чат'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Связь с чатом или сообщением
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message_text = models.TextField()
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Отметить уведомление как прочитанное"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class Project(models.Model):
    id = models.AutoField(primary_key=True)

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects")
    contributors = models.ManyToManyField(User, related_name="projects")

    image = models.ImageField(upload_to='projects')
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)

