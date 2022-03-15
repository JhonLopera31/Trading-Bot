let socket = new WebSocket("ws://localhost:3000/ws");

console.log("Conectando");

socket.onopen = () => {
    console.log("Conectado");
    socket.send("Hola desde el cliente")
};

socket.onclose = event => {
    console.log("Cerrando conexión ", event);
    socket.send("Cliente cerrado")
};

socket.onerror = error => {
    console.log("Error en el socket: ", error);
};

socket.onmessage = function (event) {
    console.log(event.data);
}