from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Avg
from .models import Vacancy, FreelanceTask, Interaction, ChatRoom, Message, Notification
from myapp.models import FreelanceTask, Currency
from myapp.currency_service import CurrencyService
# from django.contrib.auth.tokens import default_token_generator
import json
from django.contrib.auth import login, authenticate, logout

import re
from rest_framework.decorators import api_view
from rest_framework.response import Response

#auth
from .models import User
from .forms import CustomUserCreationForm
from .serializers import LoginSerializer
from rest_framework import generics
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import send_mail
from django.views import View
from django.utils.encoding import force_str, force_bytes


#----AUTH----
def auth_view(request):
    return render(request, 'auth.html')

def forgot_view(request):
    return render(request, 'forgot.html')

def reset_view(request, uidb64, token):
    return render(request, 'reset.html', {'uidb64': uidb64, 'token': token})

class RegisterAccount(generics.CreateAPIView):
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.data)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'message': 'User registered successfully!'}, status=201)
        return JsonResponse(form.errors, status=400)  # Возвращаем ошибки формы

class LoginAccount(generics.GenericAPIView):
    serializer_class = LoginSerializer  # Укажите сериализатор

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Проверка данных

        username_or_email = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Попробуем найти пользователя по имени пользователя или адресу электронной почты
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid credentials'}, status=400)

        # Проверяем пароль
        if user.check_password(password):
            login(request, user)
            return JsonResponse({'message': 'Login successful!'}, status=200)

        return JsonResponse({'error': 'Invalid credentials'}, status=400)

class PasswordResetView(View):
    def post(self, request, *args, **kwargs):
        # Получаем данные из тела запроса
        try:
            data = json.loads(request.body)  # Загружаем JSON из тела запроса
            email = data.get('email')  # Получаем email
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User  with this email does not exist'}, status=400)

        # Генерация токена и отправка письма
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://127.0.0.1:8000/reset/{uid}/{token}/"

        send_mail(
            'Password Reset Request',
            f'Вы можете сбросить пароль от вашей учётной записи по ссылке: {reset_link}\nЕсли вы не делали это, то просто проигноррируйте это сообщение',
            'simple.votings.dev@internet.ru',
            [email],
            fail_silently=False,
        )

        return JsonResponse({'message': 'Password reset email sent!'}, status=200)
    
class PasswordResetConfirmView(View):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            try:
                data = json.loads(request.body)  # Загружаем JSON из тела запроса
                new_password = data.get('new_password')
                confirm_password = data.get('confirm_password')

                # Проверка, совпадают ли пароли
                if new_password != confirm_password:
                    return JsonResponse({'error': 'Passwords do not match'}, status=400)

                user.set_password(new_password)
                user.save()
                return JsonResponse({'message': 'Password has been reset successfully!'}, status=200)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        return JsonResponse({'error': 'Invalid token or user ID'}, status=400)

@login_required
def logout_account(request):
    logout(request)
    return JsonResponse({'message': 'Logout successful!'}, status=200)



@ensure_csrf_cookie
def resume_form(request):
    """Resume constructor page (HTML).

    URL:
        /resume/

    Purpose:
        Shows the resume "constructor" (accordion with fields + live preview) for the current user.
        The page itself does NOT submit a classic HTML form. Instead, the browser periodically sends
        JSON to /api/save-resume/ (auto-save) and the backend stores it in the Resume model.

    Auth:
        Requires authenticated user. The project does not define LOGIN_URL, so we use a manual check
        and redirect to the auth page.

    Context:
        resume: Resume instance, ensured to exist via get_or_create.
    """
    # Резюме привязано к пользователю, поэтому анонимному пользователю здесь делать нечего.
    # Не используем @login_required, потому что в проекте не задан LOGIN_URL (иначе будет редирект на /accounts/login/).
    if not request.user.is_authenticated:
        return redirect('auth')

    resume, _ = Resume.objects.get_or_create(user=request.user)
    return render(request, "resume_form.html", {"resume": resume})

from .models import Resume

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_resume(request):
    """Auto-save API endpoint for the resume constructor.

    URL:
        POST /api/save-resume/

    Auth:
        DRF IsAuthenticated. Uses session auth in browser context.
        resume_form page sets CSRF cookie (@ensure_csrf_cookie) and frontend sends X-CSRFToken.

    Input:
        JSON payload with Resume fields (see resume_form.html -> collectData()).
        Example:
            {
              "full_name": "Иванов Иван",
              "position": "Backend Developer",
              "employment": "Полная",
              "work_schedule": "Удаленно",
              "salary": "150000",
              "currency": "RUB",
              "city": "Москва",
              "birth_date": "2000-01-01",
              "children": false,
              "about": "...",
              "army_service": false,
              "medical_book": false
            }

    Output:
        200 {"status": "saved"}
    """
    user = request.user
    data = request.data

    resume, _ = Resume.objects.get_or_create(user=user)

    # Основные поля
    resume.full_name = data.get("full_name", "")
    resume.position = data.get("position", "")
    resume.employment = data.get("employment", "")
    resume.work_schedule = data.get("work_schedule", "")

    # Числа/даты
    salary_raw = data.get("salary")
    try:
        resume.salary = int(salary_raw) if salary_raw not in (None, "") else None
    except (TypeError, ValueError):
        resume.salary = None

    resume.birth_date = parse_date(data.get("birth_date") or "")

    # Прочее
    resume.currency = data.get("currency", resume.currency or "RUB")
    resume.city = data.get("city", "")
    resume.citizenship = data.get("citizenship", "")
    resume.gender = data.get("gender", "")
    resume.relocation = data.get("relocation", "")
    resume.family_status = data.get("family_status", "")

    resume.children = bool(data.get("children", False))
    resume.about = data.get("about", "")

    resume.army_service = bool(data.get("army_service", False))
    resume.medical_book = bool(data.get("medical_book", False))

    resume.save()

    return Response({"status": "saved"}, status=status.HTTP_200_OK)






















def public_resume(request, username):
    """Public resume page (HTML).

    URL:
        /u/<username>/

    Purpose:
        Renders a "clean" resume view for sharing with employers.
        Uses Bootstrap layout and includes a print-friendly mode (to PDF).

    Notes:
        If the user has no resume yet, this view returns 404 (get_object_or_404).
        You can change behavior to auto-create an empty resume if needed.
    """
    user = get_object_or_404(User, username=username)
    resume = get_object_or_404(Resume, user=user)

    return render(request, "public_resume.html", {"resume": resume})









#----MAIN PAGE----


def index(request):
    """Главная страница"""
    return render(request, 'index.html')


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

    # Проверяем, есть ли чат по этой вакансии
    chat_room = None
    if request.user.is_authenticated:
        chat_room = ChatRoom.objects.filter(
            room_type='vacancy',
            vacancy=vacancy,
            participants=request.user
        ).first()

    return render(request, 'vacancy_detail.html', {
        'vacancy': vacancy,
        'applications': applications,
        'views_count': vacancy.interactions.filter(interaction_type='view').count(),
        'chat_room': chat_room,
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

    # Проверяем, есть ли чат по этой задаче
    chat_room = None
    if request.user.is_authenticated:
        chat_room = ChatRoom.objects.filter(
            room_type='task',
            task=task,
            participants=request.user
        ).first()

    return render(request, 'task_detail.html', {
        'task': task,
        'applications': applications,
        'views_count': task.interactions.filter(interaction_type='view').count(),
        'chat_room': chat_room,
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

# === ПАГИНАЦИЯ ДЛЯ ВАКАНСИЙ ===

def vacancy_list(request):
    """Список вакансий с пагинацией"""
    # Получаем параметры фильтрации и сортировки
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'created_at')
    page_size = request.GET.get('page_size', 10)
    
    # Фильтрация вакансий
    vacancies = Vacancy.objects.filter(is_active=True).select_related('employer').prefetch_related('interactions')
    
    # Поиск по названию и описанию
    if search_query:
        vacancies = vacancies.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    if sort_by == 'title_asc':
        vacancies = vacancies.order_by('title')
    elif sort_by == 'title_desc':
        vacancies = vacancies.order_by('-title')
    elif sort_by == 'date_asc':
        vacancies = vacancies.order_by('created_at')
    else:  # date_desc по умолчанию
        vacancies = vacancies.order_by('-created_at')
    
    # Проверка на пустой список
    if not vacancies.exists():
        context = {
            'page_obj': None,
            'paginator': None,
            'page_range': [],
            'page_size': int(page_size),
            'search_query': search_query,
            'sort_by': sort_by,
        }
        return render(request, 'vacancy_list.html', context)
    
    # Пагинация
    paginator = Paginator(vacancies, page_size)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Генерация диапазона страниц для отображения
    page_range = get_page_range(page_obj.number, paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'page_size': int(page_size),
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'vacancy_list.html', context)


# === ПАГИНАЦИЯ ДЛЯ ФРИЛАНС-ЗАДАЧ ===

def freelance_task_list(request):
    """Список фриланс-задач с пагинацией"""
    # Получаем параметры фильтрации и сортировки
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'deadline')
    page_size = request.GET.get('page_size', 10)
    currency_code = request.GET.get('currency', 'RUB')
    
    # Фильтрация задач
    tasks = FreelanceTask.objects.select_related('creator', 'executor', 'currency').prefetch_related('interactions')
    
    # Поиск по названию и описанию
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    if sort_by == 'title_asc':
        tasks = tasks.order_by('title')
    elif sort_by == 'title_desc':
        tasks = tasks.order_by('-title')
    elif sort_by == 'date_asc':
        tasks = tasks.order_by('created_at')
    elif sort_by == 'date_desc':
        tasks = tasks.order_by('-created_at')
    elif sort_by == 'deadline_asc':
        tasks = tasks.order_by('deadline')
    else:  # deadline по умолчанию
        tasks = tasks.order_by('deadline')
    
    # Проверка на пустой список
    if not tasks.exists():
        currencies = Currency.objects.all().order_by('code')
        
        context = {
            'page_obj': None,
            'paginator': None,
            'page_range': [],
            'page_size': int(page_size),
            'search_query': search_query,
            'sort_by': sort_by,
            'currencies': currencies,
            'selected_currency': currency_code,
        }
        return render(request, 'freelance_task_list.html', context)
    
    # Пагинация
    paginator = Paginator(tasks, page_size)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Генерация диапазона страниц для отображения
    page_range = get_page_range(page_obj.number, paginator.num_pages)
    
    # Получаем доступные валюты для конвертации
    currencies = Currency.objects.all().order_by('code')
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'page_size': int(page_size),
        'search_query': search_query,
        'sort_by': sort_by,
        'currencies': currencies,
        'selected_currency': currency_code,
    }
    
    return render(request, 'freelance_task_list.html', context)


# === ПАГИНАЦИЯ ДЛЯ ПРОЕКТОВ ===

def project_list(request):
    """Список проектов с пагинацией"""
    # Получаем параметры фильтрации и сортировки
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'created_at')
    page_size = request.GET.get('page_size', 10)
    
    # Фильтрация проектов (пока используем вакансии как пример проектов)
    # В реальности здесь должны быть объекты модели Project
    projects = Vacancy.objects.filter(is_active=True).select_related('employer').prefetch_related('interactions')
    
    # Поиск по названию и описанию
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Сортировка
    if sort_by == 'title_asc':
        projects = projects.order_by('title')
    elif sort_by == 'title_desc':
        projects = projects.order_by('-title')
    elif sort_by == 'date_asc':
        projects = projects.order_by('created_at')
    else:  # date_desc по умолчанию
        projects = projects.order_by('-created_at')
    
    # Проверка на пустой список
    if not projects.exists():
        context = {
            'page_obj': None,
            'paginator': None,
            'page_range': [],
            'page_size': int(page_size),
            'search_query': search_query,
            'sort_by': sort_by,
        }
        return render(request, 'project_list.html', context)
    
    # Пагинация
    paginator = Paginator(projects, page_size)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    # Генерация диапазона страниц для отображения
    page_range = get_page_range(page_obj.number, paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'page_size': int(page_size),
        'search_query': search_query,
        'sort_by': sort_by,
    }
    
    return render(request, 'project_list.html', context)


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def get_page_range(current_page, total_pages, max_pages=7):
    """
    Генерирует диапазон страниц для отображения в пагинации
    max_pages - максимальное количество номеров страниц для отображения
    """
    if total_pages <= max_pages:
        return range(1, total_pages + 1)
    
    # Вычисляем диапазон страниц
    start = max(1, current_page - max_pages // 2)
    end = min(total_pages, start + max_pages - 1)
    
    # Корректируем начало, если диапазон слишком сдвинулся вправо
    if end - start < max_pages - 1:
        start = max(1, end - max_pages + 1)
    
    return range(start, end + 1)


# === МЕССЕНДЖЕР ===

@login_required
def chat_list(request):
    """Список чатов пользователя"""
    # Получаем все комнаты, в которых участвует пользователь
    chat_rooms = ChatRoom.objects.filter(
        participants=request.user,
        is_active=True
    ).select_related('created_by').prefetch_related('participants')
    
    # Для каждого чата получаем последнее сообщение
    for room in chat_rooms:
        room.last_message = room.messages.order_by('-created_at').first()
        room.unread_count = room.messages.exclude(
            read_by=request.user
        ).count()
    
    context = {
        'chat_rooms': chat_rooms,
    }
    
    return render(request, 'chat/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """Страница конкретного чата"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
    
    # Помечаем все сообщения как прочитанные
    room.messages.exclude(read_by=request.user).update(is_read=True)
    for message in room.messages.exclude(read_by=request.user):
        message.mark_as_read(request.user)
    
    # Получаем сообщения чата
    messages = room.messages.select_related('sender').prefetch_related('read_by').order_by('-created_at')[:100]
    
    context = {
        'room': room,
        'messages': messages,
    }
    
    return render(request, 'chat/chat_room.html', context)


@login_required
def create_direct_chat(request, user_id):
    """Создание прямого чата с пользователем"""
    target_user = get_object_or_404(User, id=user_id)
    
    # Проверяем, есть ли уже чат между этими пользователями
    existing_rooms = ChatRoom.objects.filter(
        room_type='direct',
        participants=request.user
    ).filter(
        participants=target_user
    )
    
    if existing_rooms.exists():
        room = existing_rooms.first()
    else:
        # Создаем новый чат
        room = ChatRoom.objects.create(
            name=f"Чат с {target_user.username}",
            room_type='direct',
            created_by=request.user
        )
        room.participants.add(request.user, target_user)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def add_user_to_chat(request, room_id, user_id):
    """Добавление пользователя в чат"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
    target_user = get_object_or_404(User, id=user_id)
    
    # Проверяем, что пользователь уже не в чате
    if not room.participants.filter(id=target_user.id).exists():
        room.participants.add(target_user)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def remove_user_from_chat(request, room_id, user_id):
    """Удаление пользователя из чата"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
    target_user = get_object_or_404(User, id=user_id)
    
    # Проверяем, что пользователь в чате
    if room.participants.filter(id=target_user.id).exists():
        room.participants.remove(target_user)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def chat_users_list(request, room_id):
    """Список пользователей в чате"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
    
    # Получаем всех пользователей, кроме текущего
    other_users = User.objects.exclude(id=request.user.id)
    
    # Проверяем, кто уже в чате
    chat_participants = room.participants.all()
    
    context = {
        'room': room,
        'other_users': other_users,
        'chat_participants': chat_participants,
    }
    
    return render(request, 'chat/chat_users.html', context)


@login_required
def create_task_chat(request, task_id):
    """Создание чата по задаче"""
    task = get_object_or_404(FreelanceTask, id=task_id)
    
    # Проверяем права доступа к задаче
    if request.user != task.creator and request.user != task.executor:
        return redirect('task_detail', pk=task_id)
    
    # Проверяем, есть ли уже чат по этой задаче
    room = ChatRoom.objects.filter(
        room_type='task',
        task=task
    ).first()
    
    if not room:
        # Создаем новый чат
        room = ChatRoom.objects.create(
            name=f"Чат по задаче: {task.title}",
            room_type='task',
            task=task,
            created_by=request.user
        )
        room.participants.add(task.creator, task.executor)
    
    return redirect('chat_room', room_id=room.id)


@login_required
def create_vacancy_chat(request, vacancy_id):
    """Создание чата по вакансии"""
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    
    # Проверяем права доступа к вакансии
    if request.user != vacancy.employer and request.user != vacancy.hired_candidate:
        return redirect('vacancy_detail', pk=vacancy_id)
    
    # Проверяем, есть ли уже чат по этой вакансии
    room = ChatRoom.objects.filter(
        room_type='vacancy',
        vacancy=vacancy
    ).first()
    
    if not room:
        # Создаем новый чат
        room = ChatRoom.objects.create(
            name=f"Чат по вакансии: {vacancy.title}",
            room_type='vacancy',
            vacancy=vacancy,
            created_by=request.user
        )
        room.participants.add(vacancy.employer, vacancy.hired_candidate)
    
    return redirect('chat_room', room_id=room.id)


# === API МЕССЕНДЖЕРА ===

@require_POST
@login_required
@csrf_exempt
def send_message_api(request, room_id):
    """API для отправки сообщения"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
        
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to')
        
        if not content and message_type == 'text':
            return JsonResponse({'success': False, 'error': 'Сообщение не может быть пустым'}, status=400)
        
        # Создаем сообщение
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id
        )
        
        # Создаем уведомление для других участников
        for participant in room.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                notification_type='new_message',
                room=room,
                message=message,
                title=f"Новое сообщение от {request.user.username}",
                message_text=content[:100]
            )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': request.user.username,
                'sender_id': request.user.id,
                'created_at': message.created_at.isoformat(),
                'message_type': message.message_type,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
@login_required
def get_messages_api(request, room_id):
    """API для получения сообщений чата"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
        
        # Помечаем сообщения как прочитанные
        unread_messages = room.messages.exclude(read_by=request.user)
        for message in unread_messages:
            message.mark_as_read(request.user)
        
        # Получаем последние сообщения
        messages = room.messages.select_related('sender').prefetch_related('read_by').order_by('-created_at')[:50]
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'created_at': message.created_at.isoformat(),
                'message_type': message.message_type,
                'is_read': message.is_read,
                'read_by_count': message.read_by.count(),
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'room_name': str(room),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
@login_required
def get_chat_rooms_api(request):
    """API для получения списка чатов пользователя"""
    try:
        chat_rooms = ChatRoom.objects.filter(
            participants=request.user,
            is_active=True
        ).select_related('created_by').prefetch_related('participants')
        
        rooms_data = []
        for room in chat_rooms:
            last_message = room.messages.order_by('-created_at').first()
            unread_count = room.messages.exclude(
                read_by=request.user
            ).count()
            
            rooms_data.append({
                'id': room.id,
                'name': str(room),
                'room_type': room.room_type,
                'created_at': room.created_at.isoformat(),
                'last_message': {
                    'content': last_message.content if last_message else '',
                    'sender': last_message.sender.username if last_message else '',
                    'created_at': last_message.created_at.isoformat() if last_message else None,
                } if last_message else None,
                'unread_count': unread_count,
                'participants_count': room.participants.count(),
            })
        
        return JsonResponse({
            'success': True,
            'chat_rooms': rooms_data,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
@login_required
def get_notifications_api(request):
    """API для получения уведомлений"""
    try:
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).select_related('room', 'message', 'user').order_by('-created_at')[:20]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message_text': notification.message_text,
                'created_at': notification.created_at.isoformat(),
                'room_id': notification.room.id if notification.room else None,
                'message_id': notification.message.id if notification.message else None,
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': notifications.count(),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@csrf_exempt
def mark_notification_read_api(request, notification_id):
    """API для отметки уведомления как прочитанного"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.mark_as_read()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@login_required
@csrf_exempt
def mark_message_read_api(request, message_id):
    """API для отметки сообщения как прочитанного"""
    try:
        message = get_object_or_404(Message, id=message_id)
        
        # Проверяем, что пользователь является участником чата
        if not message.room.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
        
        message.mark_as_read(request.user)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Загружаем данные
try:
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    top_cities_ru = data["top_cities_ru"]
    job_filters = data["job_filters"]
    top_universities_ru = data["top_universities_ru"]
except (FileNotFoundError, KeyError, json.JSONDecodeError):
    # Если файл не найден или поврежден, используем заглушки
    top_cities_ru = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"]
    job_filters = {
        "Программирование": ["Backend-разработчик", "Frontend-разработчик", "Fullstack-разработчик", "Mobile-разработчик"],
        "Аналитика": ["Data Analyst", "Бизнес-аналитик", "Системный аналитик"],
        "Дизайн": ["UI/UX дизайнер", "Графический дизайнер", "Продуктовый дизайнер"]
    }
    top_universities_ru = ["МГУ", "СПбГУ", "МИФИ", "ВШЭ", "МФТИ"]


# Класс поиска
class Search:
    def __init__(self, user_tokens=None):
        self.user_tokens = user_tokens or set()

    def tokenize(self, text: str):
        if not text:
            return set()
        text = text.lower()
        words = re.findall(r"\w+", text)
        return set(words)

    def vacancy_tokens(self, vacancy):
        text = f"{vacancy.title} {vacancy.description}"
        return self.tokenize(text)

    def similarity(self, set1, set2):
        if not set1 or not set2:
            return 0
        return len(set1.intersection(set2)) / len(set1.union(set2))

    def apply_filters(self, vacancies, direction=None, profession=None, city=None):
        if direction and direction in job_filters:
            professions = job_filters[direction]
            vacancies = [v for v in vacancies if v.title in professions]
        if profession:
            vacancies = [v for v in vacancies if v.title == profession]
        if city and city in top_cities_ru:
            vacancies = [v for v in vacancies if v.city == city]
        return vacancies

    def search_vacancies(self, direction=None, profession=None, city=None, limit=20):
        # Получаем вакансии из базы данных
        vacancies = Vacancy.objects.filter(is_active=True)
        
        # Применяем фильтры
        if direction and direction in job_filters:
            professions = job_filters[direction]
            vacancies = vacancies.filter(title__in=professions)
        if profession:
            vacancies = vacancies.filter(title=profession)
        if city and city in top_cities_ru:
            vacancies = vacancies.filter(city=city)
        
        # Преобразуем в список для дальнейшей обработки
        vacancies_list = list(vacancies)
        
        # Сортируем по релевантности
        scored = [(v, self.similarity(self.user_tokens, self.vacancy_tokens(v))) for v in vacancies_list]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем отсортированные вакансии
        return [v[0] for v in scored[:limit]]


# API endpoint
@api_view(["GET"])
def search_api(request):
    # токены пользователя можно передавать через GET-параметр q
    user_query = request.GET.get("q", "")
    engine = Search(user_tokens=set(user_query.lower().split()))

    direction = request.GET.get("direction")
    profession = request.GET.get("profession")
    city = request.GET.get("city")

    results = engine.search_vacancies(direction, profession, city)
    
    # Сериализуем результаты
    from .serializers import VacancySerializer
    serializer = VacancySerializer(results, many=True)
    
    return Response(serializer.data)
