from django.urls import path
from . import views
from .views import RegisterAccount, LoginAccount, PasswordResetConfirmView, logout_account, PasswordResetView, reset_view
from .views import search_api  # импорт функции из myapp/views.py


urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    
    # Основные страницы
    path('tasks/', views.task_list, name='task_list'),
    path('api/convert/<int:task_id>/<str:target_currency>/', views.convert_currency_api, name='convert_currency_api'),
    path('currency-rates/', views.currency_rates_view, name='currency_rates'),
    
    #API SEARCH
    path('search/', search_api, name='search'),
    path('search/page/', views.search_page, name='search_page'),
    
    # Страницы с пагинацией
    path('vacancies/', views.vacancy_list, name='vacancy_list'),
    path('freelance-tasks/', views.freelance_task_list, name='freelance_task_list'),
    path('projects/', views.project_list, name='project_list'),
    
    # Детальные страницы
    path('vacancy/<int:pk>/', views.vacancy_detail, name='vacancy_detail'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    
    # Мессенджер
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/direct/<int:user_id>/', views.create_direct_chat, name='create_direct_chat'),
    path('chat/task/<int:task_id>/', views.create_task_chat, name='create_task_chat'),
    path('chat/vacancy/<int:vacancy_id>/', views.create_vacancy_chat, name='create_vacancy_chat'),
    path('chat/<int:room_id>/add-user/<int:user_id>/', views.add_user_to_chat, name='add_user_to_chat'),
    path('chat/<int:room_id>/remove-user/<int:user_id>/', views.remove_user_from_chat, name='remove_user_from_chat'),
    path('chat/<int:room_id>/users/', views.chat_users_list, name='chat_users_list'),
    
    # API мессенджера
    path('api/chat/<int:room_id>/send/', views.send_message_api, name='send_message_api'),
    path('api/chat/<int:room_id>/messages/', views.get_messages_api, name='get_messages_api'),
    path('api/chat/rooms/', views.get_chat_rooms_api, name='get_chat_rooms_api'),
    path('api/notifications/', views.get_notifications_api, name='get_notifications_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/messages/<int:message_id>/read/', views.mark_message_read_api, name='mark_message_read_api'),
    
    #API login/reg/pass reset
    path('api/register/', RegisterAccount.as_view(), name='register_account'),
    path('api/login/', LoginAccount.as_view(), name='login_account'),
    path('api/logout/', logout_account, name='logout'),
    path('api/password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('api/password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Страницы авторизации
    path('auth/', views.auth_view, name='auth'),
    path('forgot/', views.forgot_view, name='forgot'),
    path('reset/<uidb64>/<token>/', reset_view, name='reset'),

    # Проекты
    path('api/projects/create', views.create_project),
    path('api/projects/add_contributros', views.add_contributors),
    
    # Детальная страница проекта
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
]
