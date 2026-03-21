axios.defaults.BASE_URL = `http://localhost:8000`;

async function get_form(type, id) {
    let response = null;

    if (type == 'r')
        response = await axios.get(`/auth/form`, {
            registration: 1,
            id: id,
        });
    else if (type == 'l')
        response = await axios.get(`/auth/form`, {
            login: 1,
            id: id,
        });
    else
        return;

    let content = response.data;

    let node = document.querySelector(`.menu`);

    node.innerHTML = content;
}

get_form(`r`, 0);