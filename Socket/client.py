import socket
import json

HOST = '127.0.0.1'
PORT = 8080
REQUEST_FILE = "requete.json"

def build_request(req):
    method = req.get("method", "GET").upper()
    path = req.get("path", "/")
    headers = req.get("headers", {})
    body = req.get("body", "")

    lines = [f"{method} {path} HTTP/1.1"]
    for k, v in headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")  # ligne vide entre headers et body
    lines.append(body)
    return "\r\n".join(lines)

def main():
    try:
        with open(REQUEST_FILE, "r") as f:
            reqs = json.load(f)
    except FileNotFoundError:
        print(f"{REQUEST_FILE} introuvable.")
        return

    request_text = "".join(build_request(req) for req in reqs).encode("utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall(request_text)

        response = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk

    print(response.decode("utf-8", errors="replace"))


