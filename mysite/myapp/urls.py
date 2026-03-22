from django.urls import path
from . import views
from .views import search_api  # импорт функции из myapp/views.py

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('api/convert/<int:task_id>/<str:target_currency>/', views.convert_currency_api, name='convert_currency_api'),
    path('currency-rates/', views.currency_rates_view, name='currency_rates'),
    path('search/', search_api, name='search'),
]