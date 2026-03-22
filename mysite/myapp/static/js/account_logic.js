function registerAccount() {
    const username = document.getElementById('reg_name').value; // Имя пользователя
    const email = document.getElementById('reg_email').value; // Почта
    const password = document.getElementById('reg_password').value; // Пароль
    const passwordConfirm = password; // Подтверждение пароля

    console.log(username + " : " + email + " : " + password)
    fetch('/api/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            username: username,
            email: email,
            password1: password,
            password2: passwordConfirm,
        }),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        return response.json().then(err => {
            throw new Error('Registration failed: ' + JSON.stringify(err));
        });
    })
    .then(data => {
        alert(data.message); // Успешная регистрация
        window.location.href = '/';
    })
    .catch(error => {
        alert(error.message); // Ошибка регистрации
    });
}

function loginAccount() {
    const username = document.getElementById('login_name').value; // Имя пользователя
    const password = document.getElementById('login_password').value; // Пароль

    fetch('/api/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'), // Добавьте CSRF-токен, если необходимо
        },
        body: JSON.stringify({
            username: username,
            password: password,
        }),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Login failed');
    })
    .then(data => {
        alert(data.message); // Успешный вход
        window.location.href = '/';
        // Здесь вы можете перенаправить пользователя на другую страницу
    })
    .catch(error => {
        alert(error.message); // Ошибка входа
    });
}

// Функция для получения CSRF-токена из cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Проверяем, начинается ли cookie с нужного имени
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}