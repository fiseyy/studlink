from django.core.management.base import BaseCommand
from myapp.models import User, Vacancy, Currency
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Инициализация базы данных вакансиями из хардкода'

    def handle(self, *args, **kwargs):
        # Получаем или создаем валюту RUB
        currency_rub, created = Currency.objects.get_or_create(
            code='RUB',
            defaults={
                'name': 'Российский рубль',
                'symbol': '₽',
                'rate': 1.0,
                'rate_date': datetime.now().date()
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создана валюта: {currency_rub}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Используется существующая валюта: {currency_rub}'))

        # Получаем или создаем тестового работодателя
        employer, created = User.objects.get_or_create(
            username='test_employer',
            defaults={
                'email': 'employer@example.com',
                'role': 'employer',
                'university': 'Тестовый университет'
            }
        )
        
        if created:
            employer.set_password('testpassword123')
            employer.save()
            self.stdout.write(self.style.SUCCESS(f'Создан работодатель: {employer.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Используется существующий работодатель: {employer.username}'))

        # Данные вакансий из хардкода
        vacancies_data = [
            {
                "title": "Backend-разработчик",
                "city": "Москва",
                "description": "Python, Django, REST",
                "schedule": "Полный день",
                "experience": "1-3 года",
                "work_format": "Офис",
                "salary_from": 100000,
                "salary_to": 150000
            },
            {
                "title": "Frontend-разработчик",
                "city": "Санкт-Петербург",
                "description": "React, JavaScript",
                "schedule": "Полный день",
                "experience": "Без опыта",
                "work_format": "Удаленно",
                "salary_from": 80000,
                "salary_to": 120000
            },
            {
                "title": "Data Analyst",
                "city": "Москва",
                "description": "SQL, Python, аналитика данных",
                "schedule": "Гибкий график",
                "experience": "3-5 лет",
                "work_format": "Смешанный",
                "salary_from": 120000,
                "salary_to": 180000
            }
        ]

        # Создаем вакансии
        for vacancy_data in vacancies_data:
            vacancy, created = Vacancy.objects.get_or_create(
                title=vacancy_data["title"],
                city=vacancy_data["city"],
                defaults={
                    'employer': employer,
                    'description': vacancy_data["description"],
                    'expiration': datetime.now() + timedelta(days=30),
                    'schedule': vacancy_data["schedule"],
                    'experience': vacancy_data["experience"],
                    'work_format': vacancy_data["work_format"],
                    'currency': currency_rub,
                    'salary_from': vacancy_data["salary_from"],
                    'salary_to': vacancy_data["salary_to"],
                    'currency_rate_date': datetime.now().date(),
                    'currency_rate': 1.0,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана вакансия: {vacancy.title} в {vacancy.city}'))
            else:
                self.stdout.write(self.style.WARNING(f'Вакансия уже существует: {vacancy.title} в {vacancy.city}'))

        self.stdout.write(self.style.SUCCESS('Инициализация вакансий завершена!'))