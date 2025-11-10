import socket
from concurrent.futures import ThreadPoolExecutor
from Socket.HTTP_handler import HTTPHandler

def start_server(config_data, routes_data, vm_lock):
    server_vars = config_data["SERVER_CONFIG"]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_vars["HOST"], server_vars["PORT"]))
    server.listen()
    print(f"Serveur en écoute sur {server_vars["HOST"]}:{server_vars["PORT"]}")

    executor = ThreadPoolExecutor(max_workers=server_vars["MAX_WORKERS"])

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_socket.settimeout(server_vars["TIMEOUT"])
        _, client_port = client_socket.getpeername()
        client_info={"client_socket" : client_socket, "client_address" : addr, "client_port" : client_port}
        handler = HTTPHandler(client_info,config_data, routes_data,vm_lock)
        executor.submit(handler.process)
