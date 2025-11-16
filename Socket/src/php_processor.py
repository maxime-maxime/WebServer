import struct
import socket
import os

FCGI_VERSION = 1
FCGI_BEGIN_REQUEST = 1
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_END_REQUEST = 3
FCGI_RESPONDER = 1


def send_php_request(php_socket, php_env, parsed_request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 9000))  # FPM listen address

    request_id = 1

    # --- BEGIN REQUEST ---
    body = struct.pack("!HB5x", FCGI_RESPONDER, 0)  # role=1, flags=0, 5 bytes padding
    sock.sendall(make_record(FCGI_BEGIN_REQUEST, request_id, body))

    # --- PARAMS ---
    params = encode_name_value("SCRIPT_FILENAME", "/index.php") + \
             encode_name_value("REQUEST_METHOD", "GET")
    sock.sendall(make_record(FCGI_PARAMS, request_id, params))
    sock.sendall(make_record(FCGI_PARAMS, request_id, b''))  # end of params

    # --- STDIN (empty for GET) ---
    sock.sendall(make_record(FCGI_STDIN, request_id, b''))

    # --- Read response ---
    response = b''
    while True:
        header = sock.recv(8)
        if len(header) < 8:
            break
        ver, typ, req_id, clen, padlen, _ = struct.unpack("!BBHHBB", header)
        content = sock.recv(clen)
        sock.recv(padlen)  # skip padding
        if typ == FCGI_STDOUT:
            response += content
        elif typ == FCGI_END_REQUEST:
            break

    sock.close()

    # Print the PHP output
    print(response.decode(errors="ignore"))
    print("PHP request end")



def encode_name_value(name, value):
    nlen = len(name)
    vlen = len(value)
    n_bytes = struct.pack("!B", nlen) if nlen < 128 else struct.pack("!I", nlen | 0x80000000)
    v_bytes = struct.pack("!B", vlen) if vlen < 128 else struct.pack("!I", vlen | 0x80000000)
    return n_bytes + v_bytes + name.encode() + value.encode()

def make_record(type, request_id, content):
    content_len = len(content)
    padding_len = (8 - (content_len % 8)) % 8
    header = struct.pack("!BBHHBB", FCGI_VERSION, type, request_id, content_len, padding_len, 0)
    return header + content + b'\x00' * padding_len

def analyse_dynamic(data, addr, response, php_config, config, parsed_request, client_port):
        print("Analyzing php : ", addr)
        if b"<?php" not in data:
            response['Content-Type'] = "text/html"
            return

        docker_file_directory = os.path.join(
            config['DOCKER_CONFIG']['DOCKER_DIRECTORY'],
            parsed_request['PATH'][1:]
        )
        docker_file_directory = docker_file_directory.replace("\\", "/")
        print("running php file  --> ", docker_file_directory)
        php_env = set_php_config(docker_file_directory, config, parsed_request, client_port, addr)
        fpm_host, fpm_port = php_config[1].get("listen", "127.0.0.1:9000").split(":")
        fpm_port = int(fpm_port)
        php_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        php_socket.connect((fpm_host, fpm_port))
        send_php_request(php_socket, php_env, parsed_request)
        stdout = b""
        while True:
            chunk = php_socket.recv(config['SERVER_CONFIG']['PHP_BUFFER_SIZE'])
            if not chunk:
                break
            stdout += chunk

        print(stdout)
        print("php success : ", stdout.decode("utf-8", errors="replace"))
        header_bytes, body_bytes = stdout.split(b"\r\n\r\n", 1)
        if stdout.startswith(b"Status: 302 Found"):
            _,request = data.split(b":",1)
            protocol = config['SERVER_CONFIG']['HTTP_PROTOCOL'].encode()
            response = protocol + request
            raise Exception("STATUS 302, REQUEST REDICETED", response)
        response['php_header'] = header_bytes.decode()
        response['body'] = body_bytes
        response['Content-Type'] = "text/html"
        print("Analyzing php end  : ", addr)


    # --- PHP environment ---

def set_php_config(docker_file_directory, config, parsed_request, client_port,
                   addr):
        php_env = [{
    'SERVER_SOFTWARE': 'CustomPythonServer/1.0',
    'SERVER_NAME': config['SERVER_CONFIG']['HOST'],
    'SERVER_PORT': config['SERVER_CONFIG']['PORT'],
    'SERVER_PROTOCOL': 'HTTP/1.1',
    'GATEWAY_INTERFACE': 'CGI/1.1',

    'REQUEST_METHOD': parsed_request['METHOD'],
    'REQUEST_URI': parsed_request['PATH'],
    'SCRIPT_FILENAME': docker_file_directory,
    'SCRIPT_NAME': parsed_request.get('PATH', ''),
    'PATH_INFO': parsed_request.get('PATH', ''),
    'QUERY_STRING': parsed_request.get('QUERY', ''),
    'CONTENT_TYPE': parsed_request.get('Content-Type', ''),
    'CONTENT_LENGTH': str(len(parsed_request.get('body', ''))),
    'HTTP_HOST': parsed_request.get('Host', ''),
    'REDIRECT_STATUS': '200',

    'REMOTE_ADDR': addr[0],
    'REMOTE_PORT': client_port,

},""]

        minimal_env = ["METHOD", "Host", "Content-Type", "Content-Length", "PATH", 'body', 'STATUS']
        for header, value in parsed_request.items():
            if header not in minimal_env:
                key = "HTTP_" + header.upper().replace("-", "_")
                if isinstance(value, list):
                    php_env[0][key] = ", ".join(value)
                else:
                    php_env[0][key] = value

        php_env[1] = parsed_request['body']
        return php_env

if __name__ == "__main__":
    send_php_request(1,1,1)