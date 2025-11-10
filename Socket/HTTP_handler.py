import os
from datetime import datetime
import subprocess
import Socket.utils as utils
import gzip

def tracer(func):
    def wrapper(*args, **kwargs):
        print(f"@tracer :  {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# ---- Types MIME ----
ext = {
    ".html": "text/html", ".htm": "text/html; charset=UTF-8", ".css": "text/css",
    ".js": "application/javascript", ".json": "application/json",
    ".xml": "application/xml", ".txt": "text/plain", ".csv": "text/csv",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".ico": "image/x-icon", ".pdf": "application/pdf", ".zip": "application/zip",
    ".tar": "application/x-tar", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".mp4": "video/mp4", ".webm": "video/webm", ".ogg": "audio/ogg",
    ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
    ".eot": "application/vnd.ms-fontobject", ".otf": "font/otf"
}

# ---- Codes HTTP ----
http_status = {
        400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
        404: "Not Found", 405: "Method Not Allowed", 406: "Not Acceptable",
        411: "Length Required", 500: "Internal Server Error",
        501: "Not Implemented", 503: "Service Unavailable",
        200: "OK", 201: "Created", 204: "No Content", 301: "Moved Permanently",
        302: "Found", 304: "Not Modified"
}

encrypted_format = {

}

class HTTPHandler:
    def __init__(self, client_info,config_data, routes_data,vm_lock):
        self.client_socket = client_info["client_socket"]
        self.addr = client_info["client_address"]
        self.client_port = client_info["client_port"]
        self.config = config_data
        self.routes = routes_data
        self.parsed_request = {}
        self.buffer = b""
        self.vm_lock = vm_lock
        self.is_new_ext =None
        self.response={}

    # --- Body reception ---
    @tracer
    def recv_body(self):
        print(self.parsed_request)
        content_length = self.parsed_request["Content-Length"]
        if "body" not in self.parsed_request : self.parsed_request["body"] = b""
        while len(self.parsed_request["body"]) < content_length:
            chunk = self.client_socket.recv(1024)
            if not chunk:
                break
            self.parsed_request["body"] += chunk
        remaining_data = self.parsed_request["body"][content_length:]
        self.parsed_request["body"] = self.parsed_request["body"][:content_length]
        return remaining_data

    @tracer
    def parse_request(self, header_end):
        # Extraire les headers
        header_bytes = self.buffer[:header_end]  # inclut \r\n\r\n
        headers_raw = header_bytes.decode(errors="replace")

        body = self.buffer[header_end:]

        # Séparer les lignes
        lines = headers_raw.split("\r\n")

        # Extraire la ligne de requête
        try:
            method, path, version = lines[0].split(" ")
            query = None
            if "?" in path:
                path, query = path.split("?", 1)
        except ValueError:
            return {"STATUS": 400}, b""

        if not method or not path:
            return {"STATUS": 400}, b""

        # Construire le dictionnaire des headers
        pr = {"METHOD": method, "PATH": path, "VERSION": version}
        if query:
            pr["QUERY"] = query
        if pr["PATH"] == '/':
            pr["PATH"] = '/index.html'

        for line in lines[1:]:
            if ": " in line:
                name, value = line.split(": ", 1)
                pr[name] = value
        # Normalisation de certains headers
        pr["Accept"] = [item.split(";")[0].strip() for item in pr.get("Accept", "text/html").split(",")]
        pr["Accept-Encoding"] = [item.split(";")[0].strip() for item in
                                 pr.get("Accept-Encoding", "identity").split(",")]
        pr["Connection"] = pr.get("Connection", "close")
        pr["Content-Length"] = int(pr.get("Content-Length", 0))
        pr["body"] = body
        # Sauvegarde pour usage ultérieur
        self.parsed_request = pr

        return None

    # --- Logging ---
    def log_request(self):
            status,logs = utils.load_file("logs/logs.json")
            if status != 200 :
                print(f"log status : {status} --> {http_status.get(status)}")
                return
            if not isinstance(logs, list):
                logs = [logs]
            blocks_to_log = self.parsed_request.copy()
            if isinstance(blocks_to_log.get('body'), bytes):
                blocks_to_log['body'] = blocks_to_log['body'].decode("utf-8", errors="replace")
            logs.append({"time": str(datetime.now()), "addr": self.addr, "parsed_request": blocks_to_log})
            utils.save_file("logs/logs.json",logs)
            if status != 200 : print(f"log status : {status} --> {http_status.get(status)}")

    # --- Load file content ---
    @tracer
    def load_content(self, path, check_accept=True):
        extension = os.path.splitext(path)[1]
        content_type = ext.get(extension, "application/octet-stream")
        self.response["Content-Type"] = content_type
        if path[0]=='/' or path[0]=='\\' :
            path = path[1:]
        path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'], path)
        self.response["STATUS"], body = utils.load_file(path)
        print("------------------------------------------------------->   SATUS : ",self.response["STATUS"])
        if self.response["STATUS"] != 200: return
        self.response["body"] = body.encode("utf-8", errors="replace")
        if extension == '.php' or self.parsed_request["PATH"] == '/index.html' :
            self.analyse_dynamic(self.response["body"])
        if check_accept and "*/*" not in self.parsed_request.get("Accept", []) and content_type not in self.parsed_request.get("Accept", []):
            self.response["STATUS"] = 406

    @tracer
    def load_status(self, error=True):
        err_config = self.routes["STATUS_ROUTING"]
        status = self.response["STATUS"]

        if status in err_config["CUSTOM_STATUS_FILES"]:
             self.load_content(
                 os.path.join(err_config["RELATIVE_ERROR_DIRECTORY"], err_config["CUSTOM_ERROR_FILES"][status])
             )
        elif error:
             self.load_content(
                 os.path.join(err_config["RELATIVE_ERROR_DIRECTORY"], err_config["DEFAULT_ERROR_FILE"])
             )

        else:
            self.response["Content-Type"] = "text/plain"
            self.response["body"] = f"STATUS ---> {status} : {http_status.get(status)}"
            return
        if self.response["STATUS"] in {404,403,500}:
            self.response["STATUS"] = status
            self.response["Content-Type"] = "text/plain"
            self.response["body"] = f"CAN'T LOAD STATUS FILE ---> {status} : {http_status.get(status)}"

    # --- HTTP Handlers ---

    @tracer
    def handle_get(self):
        filename = self.parsed_request["PATH"]
        self.load_content(filename)
        print("heyy : ",self.response["STATUS"])
        if self.response["STATUS"] != 200:
            self.load_status()

    @tracer
    def handle_post(self):
        self.response['STATUS'] = 200
        filename = self.parsed_request["PATH"]
        try:
            self.load_content(filename)
        except FileNotFoundError:
            self.load_status()

    @tracer
    def handle_put(self):
        path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'],self.parsed_request['PATH'])
        data =self.response["body"].decode("UTF-8")
        self.response['STATUS'] = utils.save_file(path,data)
        self.load_status()


    @tracer
    def handle_delete(self):
        path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'],self.parsed_request['PATH'])
        self.response["STATUS"]=utils.delete_file(path)
        self.load_status()

    # --- PHP/JS Dynamic Processing ---
    @tracer
    def analyse_dynamic(self, data):
        with self.vm_lock:
                if b"<?php" not in data:return
                docker_file_directory = os.path.join(
                    self.config['DOCKER_CONFIG']['DOCKER_DIRECTORY'],
                    self.parsed_request['PATH'][1:]
                )
                docker_file_directory = docker_file_directory.replace("\\", "/")
                print("docker :", docker_file_directory)
                self.set_php_config(docker_file_directory)
                cmd = ["docker", "exec", "-i"]  # options avant le nom
                for var in self.response['php_config'][0]:  # -e VAR=valeur
                    cmd.extend(["-e", var])
                cmd.append("php_5.6")  # nom du conteneur
                cmd.extend(["php-cgi", "-f", docker_file_directory])
                print("------------->   DOCKER CMD ")
                print(cmd)
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = proc.communicate(input=self.response['php_config'][1])
                if stderr.decode() != "" : print("Erreur de l'interpreteur php : ", stderr.decode())
                header_bytes, body_bytes = stdout.split(b"\r\n\r\n", 1)
                self.response['php_header'] = header_bytes.decode()
                self.response['body'] = body_bytes
                self.response['Content-Type'] = "text/html"
                print("toutvabien")


    # --- PHP environment ---
    def set_php_config(self, docker_file_directory):
        php_config = [{
    'SERVER_SOFTWARE': 'CustomPythonServer/1.0',
    'SERVER_NAME': self.config['SERVER_CONFIG']['HOST'],
    'SERVER_PORT': self.config['SERVER_CONFIG']['PORT'],
    'SERVER_PROTOCOL': 'HTTP/1.1',
    'GATEWAY_INTERFACE': 'CGI/1.1',

    'REQUEST_METHOD': self.parsed_request['METHOD'],
    'REQUEST_URI': self.parsed_request['PATH'],
    'SCRIPT_FILENAME': docker_file_directory,
    'SCRIPT_NAME': self.parsed_request.get('PATH', ''),
    'PATH_INFO': self.parsed_request.get('PATH', ''),
    'QUERY_STRING': self.parsed_request.get('QUERY', ''),
    'CONTENT_TYPE': self.parsed_request.get('Content-Type', ''),
    'CONTENT_LENGTH': str(len(self.parsed_request.get('body', ''))),
    'HTTP_HOST': self.parsed_request.get('Host', ''),
    'REDIRECT_STATUS': '200',

    'REMOTE_ADDR': self.addr[0],
    'REMOTE_PORT': self.client_socket,

    'HOME': self.config['DOCKER_CONFIG']['DOCKER_DIRECTORY'],
    'PATH': self.config['DOCKER_CONFIG']['EXEC_PATH'],
    'TMPDIR': self.config['DOCKER_CONFIG']['TMPDIR'],
},""]

        minimal_env = ["METHOD", "Host", "Content-Type", "Content-Length", "PATH", 'body', 'STATUS']
        for header, value in self.parsed_request.items():
            if header not in minimal_env:
                key = "HTTP_" + header.upper().replace("-", "_")
                if isinstance(value, list):
                    php_config[0][key] = ", ".join(value)
                else:
                    php_config[0][key] = value

        php_config[1] = self.parsed_request['body']
        php_config[0] = [f"{key}={value}" for key, value in php_config[0].items()]
        self.response['php_config'] = php_config

    # --- Generate response ---
    @tracer
    def compress_body(self,body_bytes: bytes, accept_encoding: str, encryption_config: list) -> tuple[bytes, bool]:
        min_size, compress_flag, mode = encryption_config
        if compress_flag.upper() != "ON":
            return body_bytes, False

        if "gzip" in accept_encoding and len(body_bytes) >= min_size:
            compressed = gzip.compress(body_bytes, compresslevel=mode)
            if len(compressed) < len(body_bytes):
                return compressed, True
        return body_bytes, False

    def generate_response(self):
        include_body = True
        method = self.parsed_request.get("METHOD", "").upper()

        if method not in self.config["SECURITY_CONFIG"]["ALLOWED_METHODS"]:
            self.response['STATUS'] = 411
            self.load_status()

        # Traitement selon méthode
        if method in ["GET", "HEAD"]:
            self.handle_get()
            if method == "HEAD":
                include_body = False
        elif method == "POST":
            if int(self.parsed_request.get("Content-Length", 0)) == 0:
                self.parsed_request['STATUS'] = 411
                self.load_status()
            else:
                self.handle_post()
        elif method == "PUT":
            self.handle_put()
        elif method == "DELETE":
            self.handle_delete()

        # Statut et corps
        status = self.response.get("STATUS", 503)
        body_bytes = self.response.get("body", b"")
        if not isinstance(body_bytes, bytes):body_bytes.decode()

        # Analyse headers PHP s'ils existent
        headers_dict = {}
        if "php_header" in self.response:
            for line in self.response['php_header'].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers_dict[key.strip()] = value.strip()
            print("headers_dict",headers_dict)

        # Déterminer Content-Type à partir de PHP si présent
        content_type = headers_dict.get("Content-Type", self.response.get("Content-Type", "text/html"))

        # Compression
        body_bytes, encryption = self.compress_body(
            body_bytes,
            self.parsed_request.get("Accept-Encoding", ""),
            self.config['SERVER_CONFIG'].get('ENCRYPTION', [0, "OFF"])
        )

        # Construction headers HTTP
        status_text = http_status.get(status, "STATUS_ERROR")
        response_headers = [f"HTTP/1.1 {status} {status_text}",
                            f"Connection: {self.parsed_request.get('Connection', 'close')}"]

        # Ajouter headers PHP sauf Content-Length et Content-Type
        for k, v in headers_dict.items():
            if k.lower() not in ["content-length", "content-type"]:
                response_headers.append(f"{k}: {v}")

        # Content-Type et Content-Length corrects
        response_headers.append(f"Content-Type: {content_type}")
        response_headers.append(f"Content-Length: {len(body_bytes)}")
        if encryption:
            response_headers.append("Content-Encoding: gzip")

        # Finaliser headers
        response_headers_str= "\r\n".join(response_headers) + "\r\n\r\n"


        if not include_body:
            return response_headers_str.encode()
        print("header ----> ",response_headers_str.encode())
        print("body ----> ",body_bytes)
        print("here")
        if not isinstance(body_bytes, bytes):body_bytes = body_bytes.encode()
        return response_headers_str.encode() + body_bytes

    # --- Process request ---
    def process(self):
        print("processing request")
        try:
            while True:
                chunk = self.client_socket.recv(1024)
                if not chunk:
                    break
                self.buffer += chunk

                while b"\r\n\r\n" in self.buffer:
                    header_end = self.buffer.find(b"\r\n\r\n") + 4
                    # Analyse des headers
                    self.parse_request(header_end)
                    remaining_data = self.recv_body()
                    self.buffer = remaining_data
                    if self.parsed_request.get("PATH", "") in self.routes["URL_ROUTING"]:
                        self.redirect_url()
                        break
                    response = self.generate_response()
                    self.log_request()
                    #print("answer ---> ",response)
                    print("REQUEST SEND")
                    self.client_socket.sendall(response)

                    if self.parsed_request["Connection"].lower() == "close":
                        self.client_socket.close()
                        return
        except Exception as e:
            try:
                print(e.args)
                body_bytes = "Oupsi... on a un problème :/".encode()
                response = (
                        b"HTTP/1.1 500 Internal Server Error\r\n"
                        b"Content-Type: text/plain\r\n"
                        b"Content-Length: " + str(len(body_bytes)).encode() + b"\r\n"
                        b"Connection: close\r\n\r\n" +
                        body_bytes
                )
                self.client_socket.sendall(response)
            finally:
                self.client_socket.close()

    def redirect_url(self):
        response_headers = (
            "HTTP/1.1 302 Found\r\n"
            "Location: "+self.routes["URL_ROUTING"][self.parsed_request["PATH"]]+"\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        )
        self.client_socket.sendall(response_headers.encode())
        self.client_socket.close()
