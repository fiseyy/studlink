from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('api/convert/<int:task_id>/<str:target_currency>/', views.convert_currency_api, name='convert_currency_api'),
    path('currency-rates/', views.currency_rates_view, name='currency_rates'),
]