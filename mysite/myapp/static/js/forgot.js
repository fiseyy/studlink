function sendPasswordResetEmail() {
    const email = document.querySelector('input[placeholder="email"]').value; // Получаем email из поля ввода

    fetch('/api/password_reset/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ email: email }),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Password reset failed');
    })
    .then(data => {
        alert(data.message); // Успешное отправление письма
    })
    .catch(error => {
        alert(error.message); // Ошибка отправки
    });
}