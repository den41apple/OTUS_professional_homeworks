import logging
import queue
import socket
import threading

from request_handler import RequestHandler

from config import NUM_WORKERS, IP_ADDR, PORT


def start_server():
    """Запуск сервера"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP_ADDR, PORT))
    server.listen(NUM_WORKERS)
    logging.info(f"Прослушивание {IP_ADDR}:{PORT}")

    try:
        connection_queue = queue.Queue(NUM_WORKERS)
        for worker_i in range(NUM_WORKERS):
            worker = threading.Thread(target=RequestHandler,
                                      args=(worker_i, connection_queue))
            worker.start()

        while True:
            client_sock, address = server.accept()
            ip, port = address
            logging.info(f"Соединение на {ip}:{port}")
            connection_queue.put(client_sock)

    except KeyboardInterrupt:
        logging.info('Сервер остановлен')


if __name__ == '__main__':
    start_server()
