import os
import json
import time


encrypted_format = (
    ".zip", ".gz", ".bz2", ".7z", ".rar",
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".ico",
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".tar", ".tar.gz", ".tgz",
    ".exe", ".dll", ".bin"
)




def tracer(func):
    def wrapper(*args, **kwargs):
        print(f"    trying to {func.__name__}")
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"durée pour {func.__name__} : {end - start}")
        return result
    return wrapper

def load_file(path, log=True):
    local_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(local_path, path)
    path = path.replace("/", "\\")
    if log :print(f"loading {path}")
    extension = os.path.splitext(path)[1].lower()

    if not os.path.exists(path):
        return 404, None

    try:
        if extension in encrypted_format:
            with open(path, 'rb') as f:
                # mode binaire pour images
                content = f.read()
                return 200, content
        else:
            with open(path, 'r', encoding="utf-8") as f:
                if extension == ".json":
                    try:
                        return 200, json.load(f)
                    except json.JSONDecodeError:
                        f.seek(0)
                        return 200, f.read()
                else:
                    return 200, f.read()
    except PermissionError:
        return 403, None
    except Exception:
        return 500, None

def save_file(path, data, log=True):

    local_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(local_path, path)
    path = path.replace("/", "\\")
    if log :print(f"saving {path}")

    extension = os.path.splitext(path)[1]

    file_exists = os.path.exists(path)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            if extension == ".json":
                # Vérifie que les données sont un JSON valide
                if not isinstance(data, (dict, list)):
                    raise ValueError("Les données doivent être un dict ou une list pour JSON")
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(data))

    except ValueError:
        return 400  # Bad Request
    except PermissionError:
        return 403  # Forbidden
    except Exception:
        return 500  # Internal Server Error

    return 201 if not file_exists else 200

def delete_file(path, log=True):
    local_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(local_path, path)
    path = path.replace("/", "\\")
    if log :print(f"deleting {path}")


    try:
        if not os.path.exists(path):
            return 404  # Not Found
        if not os.access(path, os.W_OK):
            return 403  # Forbidden
        os.remove(path)
        return 204  # No Content
    except IsADirectoryError:
        return 400  # Bad Request
    except PermissionError:
        return 403  # Forbidden
    except Exception:
        return 500  # Internal Server Error