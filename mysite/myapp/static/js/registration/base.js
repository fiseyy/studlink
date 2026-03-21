axios.defaults.BASE_URL = `http://localhost:8000`;

async function get_step(step) {
    console.log(step);
    let response = await axios.get(`/registration/${step}`);
    let content = response.data;

    let node = document.querySelector('.menu');

    node.innerHTML = content;
}

get_step(0);