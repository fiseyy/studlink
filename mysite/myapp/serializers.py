from rest_framework import serializers
from .models import User, Vacancy

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ['id', 'title', 'city', 'description', 'employer', 'created_at', 'salary_from', 'salary_to', 'currency']
