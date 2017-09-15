import socket
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(threadName)-10s) %(message)s'
)

def client_handler(sock, address, port):
    while True:
        try:
            data = sock.recv(1024)
            logging.debug(f"Recv: {data} from {address}:{port}")
        except OSError:
            break

        if len(data) == 0:
            break

        sent_data = data
        while True:
            sent_len = sock.send(data)
            if sent_len == len(data):
                break
            sent_data = sent_data[sent_len:]
        logging.debug(f"Send: {data} to {address}:{port}")

    sock.close()
    logging.debug(f"Bye-bye: {address}:{port}")

def main(host='localhost', port=9090):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    serversocket.bind((host, port))
    serversocket.listen(5)

    while True:
        try:
            client_sock, (client_address, client_port) = serversocket.accept()
            logging.debug(f"New client {client_address}:{client_port}")
            client_thread = threading.Thread(target=client_handler,
                args=(client_sock, client_address, client_port))
            client_thread.daemon = True
            client_thread.start()
        except:
            pass


if __name__ == "__main__":
    main()