from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, error_messages={
        'required': 'Введите имя'
    })
    last_name = forms.CharField(max_length=30, required=True, error_messages={
        'required': 'Введите фамилию'
    })
    email = forms.EmailField(required=True, error_messages={
        'required': 'Введите email',
        'invalid': 'Введите корректный email'
    })

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    # Проверка email на уникальность
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not(first_name.isalpha()):
            raise forms.ValidationError("Неверное имя")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not(last_name.isalpha()):
            raise forms.ValidationError("Неверная фамилия")
        return first_name

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError("Пароль должен быть от 8 символов")

    # Проверка username
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise forms.ValidationError("Никнейм должен состоять из 4 и более символов")
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Этот никнейм уже используется")
        return username