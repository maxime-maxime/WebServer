import subprocess
import os

def start_docker(docker_config, www_directory, php_config):
    """Crée et lance le conteneur Docker si nécessaire."""

    subprocess.run(["docker", "rm", "-f", docker_config["CONTAINER_NAME"]],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    host_path = os.path.join(docker_config['LOCAL_PATH'], www_directory)
    container_path = docker_config['DOCKER_DIRECTORY']

    fpm_host, fpm_port = php_config[1].get("listen", "127.0.0.1:9000").split(":")
    fpm_port = int(fpm_port)

    print("LAUNCHING CONTAINER IN PATH :", host_path, ":", container_path)

    subprocess.run([
        "docker", "run",
        "-v", f"{host_path}:{container_path}",
        "--name", docker_config["CONTAINER_NAME"],
        "-p", f"{fpm_port}:9000",
        "-e", f"HOME={docker_config['DOCKER_DIRECTORY']}",
        "-e", f"PATH={docker_config['EXEC_PATH']}",
        "-e", f"TMPDIR={docker_config['TMPDIR']}",
        "-d",
        docker_config["IMAGE_NAME"],
        "/usr/sbin/php-fpm8.4", "-F"
    ])

    print(f"DOCKER LAUNCHED WITH PHP-FPM ON PORT {fpm_port}")
