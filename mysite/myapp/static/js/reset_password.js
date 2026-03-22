function resetPassword(event, uidb64, token) {
    event.preventDefault(); // Предотвращаем стандартное поведение формы

    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    fetch(`/api/password_reset_confirm/${uidb64}/${token}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'), // Если используете CSRF
        },
        body: JSON.stringify({
            new_password: newPassword,
            confirm_password: confirmPassword,
        }),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Password reset failed');
    })
    .then(data => {
        alert(data.message);
        // Перенаправление или другие действия после успешного сброса пароля
    })
    .catch(error => {
        alert(error.message);
    });
}