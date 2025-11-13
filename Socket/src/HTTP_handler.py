import os
from datetime import datetime
import subprocess
import Socket.src.utils as utils
from Socket.src.utils import tracer
import gzip
from email.utils import format_datetime
import datetime
import xxhash


static_files = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/x-icon",
    "image/bmp",
    "image/tiff",
    "image/avif",
    "font/woff",
    "font/woff2",
    "font/ttf",
    "font/otf",
    "application/vnd.ms-fontobject",
    "application/javascript",
    "text/javascript",
    "text/css",
    "text/x-scss",
    "text/x-less",
    "video/mp4",
    "video/webm",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/mp2t",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/xml",
    "application/json",
    "application/x-yaml",
    "application/zip",
    "application/x-rar-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-7z-compressed",
    "application/wasm",
    "text/markdown",
    "text/yaml",
    "text/calendar"
]



# ---- Types MIME ----
ext = {
    ".html": "text/html",
    ".htm": "text/html; charset=UTF-8",
    ".css": "text/css",
    ".scss": "text/css",
    ".less": "text/css",
    ".js": "application/javascript",
    ".mjs": "application/javascript",
    ".map": "application/json",
    ".json": "application/json",
    ".xml": "application/xml",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".md": "text/markdown",
    ".yml": "text/yaml",
    ".yaml": "text/yaml",
    ".log": "text/plain",
    ".cfg": "text/plain",
    ".ini": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".avif": "image/avif",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".rar": "application/x-rar-compressed",
    ".7z": "application/x-7z-compressed",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".eot": "application/vnd.ms-fontobject",
    ".wasm": "application/wasm",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".ics": "text/calendar",
    ".ts": "video/mp2t"
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

# ---- Encrypted formats ----


class HTTPHandler:
    def __init__(self, client_info,config_data, routes_data,vm_lock,log_lock):
        self.client_socket = client_info["client_socket"]
        self.addr = client_info["client_address"]
        self.client_port = client_info["client_port"]
        self.config = config_data
        self.routes = routes_data
        self.parsed_request = {}
        self.buffer = bytearray()
        self.vm_lock = vm_lock
        self.log_lock = log_lock
        self.is_new_ext =None
        self.response={}

    # --- Body reception ---
    def recv_body(self):
        content_length = self.parsed_request["Content-Length"]
        if "body" not in self.parsed_request:
            self.parsed_request["body"] = bytearray()
        while len(self.parsed_request["body"]) < content_length:
            chunk = self.client_socket.recv(1024)
            if not chunk:
                break
            self.parsed_request["body"].extend(chunk)
        remaining_data = self.parsed_request["body"][content_length:]
        self.parsed_request["body"] = self.parsed_request["body"][:content_length]
        return self.parsed_request["body"][content_length:]

    def extract_header_bytes(self):
        """Retourne les bytes des headers et la partie restante du buffer."""
        header_end = self.buffer.find(b"\r\n\r\n")
        if header_end == -1:  # pas trouvé
            return None, self.buffer
        header_end += 4
        return self.buffer[:header_end], self.buffer[header_end:]


    def parse_request_line(self, header_lines):
        """Parse la première ligne: méthode, path, version et query."""
        method, path, version = header_lines[0].split(" ")
        query = None
        if "?" in path:
            path, query = path.split("?", 1)
        return method, path, version, query

    def parse_headers(self, header_lines):
        """Retourne un dict des headers bruts."""
        headers = {}
        for line in header_lines[1:]:
            if ": " in line:
                name, value = line.split(": ", 1)
                headers[name] = value
        return headers

    def normalize_headers(self, headers):
        """Normalise certains headers et valeurs par défaut."""
        headers["Accept"] = [item.split(";")[0].strip() for item in headers.get("Accept", "text/html").split(",")]
        headers["Accept-Encoding"] = [item.split(";")[0].strip() for item in
                                      headers.get("Accept-Encoding", "identity").split(",")]
        headers["Connection"] = headers.get("Connection", "close")
        headers["Content-Length"] = int(headers.get("Content-Length", 0))
        return headers

    def handle_special_headers(self, headers):
        """Traite les headers spéciaux comme Expect."""
        if headers.get("Expect", "").lower() == "100-continue":
            self.client_socket.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
        return headers

    def parse_request(self):
        """Parse la requête complète depuis self.buffer."""
        header_bytes, body = self.extract_header_bytes()
        if header_bytes is None:
            return None  # headers incomplets

        header_lines = header_bytes.decode(errors="replace").split("\r\n")
        try:
            method, path, version, query = self.parse_request_line(header_lines)
        except ValueError:
            # Ligne de requête incomplète; attendre plus de données
            return None

        headers = self.parse_headers(header_lines)
        headers = self.normalize_headers(headers)
        headers = self.handle_special_headers(headers)

        # Corps en bytearray pour permettre l'extension dans recv_body()
        request = {"METHOD": method, "PATH": path, "VERSION": version, "body": bytearray(body), **headers}
        if query:
            request["QUERY"] = query

        return request

    # --- Logging ---
    def log_request(self):

            status,logs = utils.load_file("logs/logs.json", log=False)
            if status != 200 :
                print(f"WARNING : CAN'T LOAD LOGS : STATUS : {status}  --> {http_status.get(status)}")
                return
            if not isinstance(logs, list):
                logs = [logs]
            blocks_to_log = self.parsed_request.copy()
            body_field = blocks_to_log.get('body')
            if isinstance(body_field, (bytes, bytearray)):
                    blocks_to_log['body'] = bytes(body_field).decode("utf-8", errors="replace")
            logs.append({"time": str(datetime.datetime.now(datetime.timezone.utc)), "addr": self.addr, "parsed_request": blocks_to_log})

            with self.log_lock :
                status = utils.save_file("logs/logs.json", logs)
            if status != 200 : print(f"WARNING : CAN'T SAVE LOGS  --> STATUS : {status}  --> {http_status.get(status)}")

    # --- Load file content ---
    def load_content(self, path, check_accept=True):
        if path.endswith('/'):
            path = path + 'index.php'
            if path[0] == '/' or path[0] == '\\':
                path = path[1:]
                print("path : ",path)
            path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'], path)
            self.response["STATUS"], body = utils.load_file(path)
            if self.response["STATUS"] == 200 : self.parsed_request["PATH"] = "/index.php"
            elif self.response["STATUS"] != 200:
                path = path.replace("php", "html")
                self.response["STATUS"], body = utils.load_file(path)
                self.parsed_request["PATH"] = "/index.html"
                if self.response["STATUS"] != 200:
                    return
        else :
            if path[0]=='/' or path[0]=='\\' :
                path = path[1:]
            path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'], path)
            self.response["STATUS"], body = utils.load_file(path)
            if self.response["STATUS"] != 200: return
        extension = os.path.splitext(path)[1]
        content_type = ext.get(extension, "application/octet-stream")
        self.response["Content-Type"] = content_type
        if extension == '.js' :
                body = body.replace("<script>", "")
                body = body.replace("</script>", "")
        self.response["body"] = body.encode("utf-8", errors="replace") if not isinstance(body, bytes) else body
        if self.response["STATUS"] != 200: return
        if extension == '.php' :
            self.analyse_dynamic(self.response["body"])
        if self.response["STATUS"]== 304 :
            current_hash = self.define_cache(self.response["body"], check=True)
            if current_hash == self.parsed_request.get("If-None-Match", ""):
                raise Exception ("NOT MODIFIED",current_hash)
        if check_accept and "*/*" not in self.parsed_request.get("Accept", []) and content_type not in self.parsed_request.get("Accept", []):
            self.response["STATUS"] = 406

    def load_status(self, error=True):
        err_config = self.routes["STATUS_ROUTING"]
        status = self.response["STATUS"]
        print("redirecting to status page ---> STATUS : ",status)

        if status in err_config["CUSTOM_STATUS_FILES"]:
             print(err_config["CUSTOM_ERROR_FILES"][status])
             self.load_content(
                 os.path.join(err_config["RELATIVE_ERROR_DIRECTORY"], err_config["CUSTOM_ERROR_FILES"][status])
             )
        elif error:
             self.load_content(
                 os.path.join(err_config["RELATIVE_ERROR_DIRECTORY"], err_config["DEFAULT_ERROR_FILE"])
             )

        else:
            self.response["Content-Type"] = "text/plain"
            self.response["body"] = f"STATUS  ---> {status} : {http_status.get(status)}"
            return

        if self.response["STATUS"] in {404,403,500}:
            self.response["STATUS"] = status
            self.response["Content-Type"] = "text/plain"
            self.response["body"] = f"WARNING : CAN'T LOAD DEFAULT ERROR PAGE  ---> STATUS : {self.response["STATUS"]} : {http_status.get(status)}".encode("utf-8", errors="replace")
            print("--------------------------->  ",self.response["body"],"   <---------------------------")

    # --- HTTP Handlers ---

    def handle_get(self):
        filename = self.parsed_request["PATH"]
        self.load_content(filename)
        if self.response["STATUS"] != 200:
            self.load_status()

    def handle_post(self):
        self.response['STATUS'] = 200
        filename = self.parsed_request["PATH"]
        try:
            self.load_content(filename)
        except FileNotFoundError:
            self.load_status()

    def handle_put(self):
        path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'],self.parsed_request['PATH'])
        data =self.response["body"].decode("UTF-8")
        self.response['STATUS'] = utils.save_file(path, data)
        self.load_status()

    def handle_delete(self):
        path = os.path.join(self.config['SERVER_CONFIG']['WWW_DIRECTORY'],self.parsed_request['PATH'])
        self.response["STATUS"]= utils.delete_file(path)
        self.load_status()

    # --- PHP/JS Dynamic Processing ---
    @tracer
    def analyse_dynamic(self, data):
        print("Analyzing php : ", self.addr)
        if b"<?php" not in data:
            self.response['Content-Type'] = "text/html"
            return
        docker_file_directory = os.path.join(
            self.config['DOCKER_CONFIG']['DOCKER_DIRECTORY'],
            self.parsed_request['PATH'][1:]
        )
        docker_file_directory = docker_file_directory.replace("\\", "/")
        print("running php file  --> ", docker_file_directory)
        self.set_php_config(docker_file_directory)
        cmd = ["docker", "exec", "-i"]  # options avant le nom
        for var in self.response['php_config'][0]:  # -e VAR=valeur
            cmd.extend(["-e", var])
        cmd.append(self.config['DOCKER_CONFIG']['CONTAINER_NAME'])  # nom du conteneur
        cmd.extend(["php-cgi", "-f", docker_file_directory])
        print("cmd : ",cmd)
        with self.vm_lock:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = proc.communicate(input=self.response['php_config'][1])
        print("php success")
        #print("stdout : ",stdout)
        if stderr.decode() != "" : print("PHP INTERPRETOR ERROR : ", stderr.decode())
        if stderr.decode() != "" : print("Erreur de l'interpreteur php : ", stderr.decode())
        header_bytes, body_bytes = stdout.split(b"\r\n\r\n", 1)
        if stdout.startswith(b"Status: 302 Found"):
            _,request = data.split(b":",1)
            protocol = self.config['SERVER_CONFIG']['HTTP_PROTOCOL'].encode()
            response = protocol + request
            raise Exception("STATUS 302, REQUEST REDICETED", response)
        self.response['php_header'] = header_bytes.decode()
        self.response['body'] = body_bytes
        self.response['Content-Type'] = "text/html"
        print("Analyzing php end  : ", self.addr)


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
    'REMOTE_PORT': self.client_port,

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
        print("PHP CONFIG SET", self.response['php_config'])

    # --- Generate response ---

    def compress_body(self,body_bytes: bytes, accept_encoding: str, encryption_config: list, content_encoding: str) -> tuple[bytes, bool]:
        if content_encoding != "":
            print('already encrypted')
            return body_bytes, True
        min_size, compress_flag, mode = encryption_config
        if compress_flag.upper() != "ON":
            print("compression disabled")
            return body_bytes, False

        if "gzip" in accept_encoding and len(body_bytes) >= min_size and self.response['Content-Type'] not in utils.encrypted_format:
            compressed = gzip.compress(body_bytes, compresslevel=mode)
            if len(compressed) < len(body_bytes):
                print("file compressed")
                return compressed, True
            print("compression disabled")
        return body_bytes, False

    def define_cache(self, data, check=False):
        if check :
            return xxhash.xxh64(data).hexdigest()

        dt = datetime.datetime.now(datetime.timezone.utc)
        date_http = format_datetime(dt)
        h = xxhash.xxh64(data).hexdigest()
        return [
            f"Cache-Control: public, max-age={self.config['SERVER_CONFIG']['CACHE'][1]}, immutable",
            f"ETag: {h}",
            f"Last-Modified: {date_http}"
        ]


    def check_method(self):
        method = self.parsed_request.get("METHOD", "").upper()
        if method not in self.config["SECURITY_CONFIG"]["ALLOWED_METHODS"]:
            self.response['STATUS'] = 411
            self.load_status()
        return method


    def handle_method(self, method):
        if method in ["GET", "HEAD"]:
            self.handle_get()
            return method == "HEAD"
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
        return False


    def parse_php_headers(self):
        headers_dict = {}
        if "php_header" in self.response:
            for line in self.response['php_header'].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    if key == "Status":
                        self.response["SPECIAL_STATUS"] = value
                    headers_dict[key.strip()] = value.strip()
        return headers_dict


    def build_headers(self, body_bytes, headers_dict, include_body):
        status = self.response.get("STATUS", 503)
        status_text = self.response.get("SPECIAL_STATUS", "") or f"{status} {http_status.get(status, 'STATUS_ERROR')}"

        content_type = headers_dict.get("Content-Type", self.response.get("Content-Type", "text/html"))
        content_encoding = headers_dict.get("Content-Encoding", self.response.get("Content-Encoding", ""))

        body_bytes, encryption = self.compress_body(
            body_bytes,
            self.parsed_request.get("Accept-Encoding", ""),
            self.config['SERVER_CONFIG'].get('ENCRYPTION', [0, "OFF"]),
            content_encoding
        )

        headers = [f"HTTP/1.1 {status_text}",
                   f"Connection: {self.parsed_request.get('Connection', 'close')}"]

        for k, v in headers_dict.items():
            if k.lower() not in ["content-length", "content-type"]:
                headers.append(f"{k}: {v}")

        headers.append(f"Content-Type: {content_type}")
        headers.append(f"Content-Length: {len(body_bytes)}")
        if encryption and content_encoding == "":
            headers.append("Content-Encoding: gzip")

        if self.config['SERVER_CONFIG']['CACHE'][0].upper() == "ON" and content_type in static_files:
            headers.extend(self.define_cache(body_bytes))

        headers_str = "\r\n".join(headers) + "\r\n\r\n"
        return headers_str.encode(), body_bytes

    def generate_response(self):
        method = self.check_method()
        include_body = not self.handle_method(method)

        body_bytes = self.response.get("body", b"")
        if not isinstance(body_bytes, bytes):
            body_bytes = body_bytes.encode()

        headers_dict = self.parse_php_headers()
        headers_encoded, body_bytes = self.build_headers(body_bytes, headers_dict, include_body)

        if include_body:
            return headers_encoded + body_bytes
        return headers_encoded

    # --- Process request ---
    @tracer
    def gather_requests(self):
        print("gathering req : ", self.addr)
        try:
            while True:
                chunk = self.client_socket.recv(8192)
                if not chunk:
                    break
                self.buffer.extend(chunk)

                while b"\r\n\r\n" in self.buffer:
                    parsed = self.parse_request()
                    if parsed is None:
                        # Headers incomplets, lire plus de données
                        break
                    # Assigner la requête parsée pour les étapes suivantes
                    self.parsed_request = parsed
                    remaining_data = self.recv_body()
                    self.buffer = bytearray(remaining_data)

                    if self.parsed_request.get("PATH", "") in self.routes["URL_ROUTING"]:
                        self.redirect_url()
                        break
                    response = self.generate_response()
                    print("here")

                    #print("-------------------------------------------------------")
                    #print(response)
                    print("REQUEST SEND")
                    self.client_socket.sendall(response)
                    self.log_request()
                    close = self.parsed_request["Connection"]
                    self.parsed_request={}
                    self.response={}
                    print("gathering req end: ", self.addr)
                    if close.lower() == "close":
                        self.client_socket.close()
                        return
        except Exception as e:
            if e.args[0] == "NOT MODIFIED" :
                try :
                    print("STATUS 304 : NOT MODIFIED")
                    response = (
                            b"HTTP/1.1 304 Not Modifiedr\r\n"
                            b"If-None-Match: " + e.args[1].encode() + b"\r\n"
                    )
                    self.client_socket.sendall(response)
                    print("REQUEST SEND")
                    return
                except Exception as e :
                    pass
            if e.args[0] == "STATUS 302, REQUEST REDICETED":
                try :
                    print("STATUS 302 : REQUEST REDICETED")
                    response = e.args[1]
                    self.client_socket.sendall(response)
                    print("REQUEST SEND")
                    return
                except Exception as e :
                    pass

            try:
                print("INTERNAL SERVER ERROR : ", e.args)
                body_bytes = "Oupsi... on a un souci :/".encode()
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

    @tracer
    def redirect_url(self):
        print("REQUEST REDIRECTED FROM INTERNAL RULES")
        response_headers = (
            "HTTP/1.1 302 Found\r\n"
            "Location: "+self.routes["URL_ROUTING"][self.parsed_request["PATH"]]+"\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        )
        self.client_socket.sendall(response_headers.encode())
        print("REQUEST SEND")
        self.client_socket.close()



