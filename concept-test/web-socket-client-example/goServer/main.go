package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func setupRoutes() {
	http.HandleFunc("/", home)
	http.HandleFunc("/ws", wsHome)
}

func home(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Holis!!")
}

func wsHome(w http.ResponseWriter, r *http.Request) {
	upgrader.CheckOrigin = func(r *http.Request) bool { return true }

	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println(err)
	}

	log.Println("Client Connected")
	err = ws.WriteMessage(1, []byte("Hi Client!"))
	if err != nil {
		log.Println(err)
	}
	reader(ws)
}

func reader(conn *websocket.Conn) {
	for {
		messageType, p, err := conn.ReadMessage()
		if err != nil {
			log.Println(err)
			return
		}
		fmt.Println(string(p))

		if err := conn.WriteMessage(messageType, []byte("Hola desde GO -->"+string(p))); err != nil {
			log.Println(err)
			return
		}
	}
}

func main() {
	fmt.Println("ohla")
	setupRoutes()
	log.Fatal(http.ListenAndServe(":3000", nil))
}
