from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from .models import Vacancy, FreelanceTask, Interaction

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
