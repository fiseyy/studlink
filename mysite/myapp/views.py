from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from .models import Vacancy, FreelanceTask, Interaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from myapp.models import FreelanceTask, Currency
from myapp.currency_service import CurrencyService

def vacancy_detail(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)

    # создаём запись просмотра, если пользователь авторизован
    if request.user.is_authenticated:
        Interaction.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(Vacancy),
            object_id=vacancy.id,
            interaction_type='view'
        )

    # получаем отклики на вакансию
    applications = vacancy.interactions.filter(interaction_type='apply')

    return render(request, 'vacancy_detail.html', {
        'vacancy': vacancy,
        'applications': applications,
        'views_count': vacancy.interactions.filter(interaction_type='view').count()
    })

def apply_vacancy(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)

    if request.user.is_authenticated and request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')

        Interaction.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(Vacancy),
            object_id=vacancy.id,
            interaction_type='apply',
            cover_letter=cover_letter
        )

        return redirect('vacancy_detail', pk=vacancy.id)

def task_detail(request, pk):
    task = get_object_or_404(FreelanceTask, pk=pk)

    if request.user.is_authenticated:
        Interaction.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(FreelanceTask),
            object_id=task.id,
            interaction_type='view'
        )

    applications = task.interactions.filter(interaction_type='apply')

    return render(request, 'task_detail.html', {
        'task': task,
        'applications': applications,
        'views_count': task.interactions.filter(interaction_type='view').count()
    })

def task_list(request):
    """Отображение списка задач с возможностью смены валюты"""
    # Получаем выбранную валюту из GET параметров или используем RUB по умолчанию
    selected_currency = request.GET.get('currency', 'RUB')
    
    # Получаем все задачи
    tasks = FreelanceTask.objects.select_related('creator', 'executor', 'currency').all()
    
    # Получаем все доступные валюты
    currencies = Currency.objects.all().order_by('code')
    
    context = {
        'tasks': tasks,
        'currencies': currencies,
        'selected_currency': selected_currency,
    }
    
    return render(request, 'examples/task_list.html', context)

@require_GET
def convert_currency_api(request, task_id, target_currency):
    """API для конвертации стоимости задачи в указанную валюту"""
    try:
        task = FreelanceTask.objects.get(id=task_id)
        currency = Currency.objects.get(code=target_currency)
        
        service = CurrencyService()
        
        # Получаем стоимость в базовой валюте (RUB)
        cost_rub = service.get_task_cost_in_base_currency(task)
        
        # Конвертируем в целевую валюту
        # Для этого нужно знать курс целевой валюты к базовой
        target_rate = task.currency_rate_date  # Здесь нужно получать курс целевой валюты
        
        # Пока возвращаем заглушку
        converted_amount = cost_rub  # Нужно реальное вычисление
        
        formatted_amount = service.format_currency(converted_amount, target_currency)
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'target_currency': target_currency,
            'currency_name': currency.name,
            'formatted_amount': formatted_amount,
            'amount': converted_amount,
        })
        
    except (FreelanceTask.DoesNotExist, Currency.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': 'Task or currency not found'
        }, status=404)

def currency_rates_view(request):
    """Страница просмотра текущих курсов валют"""
    service = CurrencyService()
    
    # Получаем все валюты с их курсами из модели Currency
    currencies = Currency.objects.all()
    
    currency_data = []
    for currency in currencies:
        currency_data.append({
            'code': currency.code,
            'name': currency.name,
            'symbol': currency.symbol,
            'rate': currency.rate,
            'rate_date': currency.rate_date,
        })
    
    context = {
        'currencies': currency_data,
        'base_currency': service.base_currency,
    }
    
    return render(request, 'examples/currency_rates.html', context)
