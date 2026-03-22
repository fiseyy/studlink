function logoutAccount() {
    fetch('/api/logout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'), // Добавьте CSRF-токен
        },
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Logout failed');
    })
    .then(data => {
        alert(data.message); // Успешный логаут
        // Здесь вы можете перенаправить пользователя на страницу входа или главную страницу
        window.location.href = '/'; // Пример перенаправления на главную страницу
    })
    .catch(error => {
        alert(error.message); // Ошибка логаута
    });
}

// Меню профиля (по клику на аватар)
document.addEventListener('DOMContentLoaded', function() {
    const profileAvatar = document.getElementById('profile-avatar');
    const dropdownMenu = document.getElementById('dropdown-menu');
    
    if (profileAvatar && dropdownMenu) {
        profileAvatar.addEventListener('click', function() {
            dropdownMenu.classList.toggle('show');
        });
        
        // Закрытие меню при клике вне его
        document.addEventListener('click', function(event) {
            if (!profileAvatar.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
});

// Функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
