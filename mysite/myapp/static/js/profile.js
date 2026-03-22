function getCSRF() {
    cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.split('=');
        if (cookie[0] == 'csrftoken')
            return cookie[1]
    }
}

async function change_profile() {
    let username = document.querySelector(`#username1`).value;
    let name = document.querySelector(`#name1`).value;
    let surname = document.querySelector(`#surname1`).value;
    let email = document.querySelector(`#mail1`).value;

    let response = await axios.post(`http://localhost:8000/api/user/change_data`, {
        username: username,
        name: name,
        surname: surname,
        email: email,
    },
    {
        headers: {
            'X-CSRFToken': getCSRF(),
        },
    });
    let answer = response.data;
}