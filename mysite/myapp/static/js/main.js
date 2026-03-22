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