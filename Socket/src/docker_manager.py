import subprocess
import os

def start_docker(docker_config, www_directory):
        """Crée et lance le conteneur Docker si nécessaire."""
        # Supprimer le conteneur existant
        #subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNUL

        subprocess.run(["docker", "rm", "-f", docker_config["CONTAINER_NAME"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        host_path = os.path.join(docker_config['LOCAL_PATH'], www_directory)
        container_path = docker_config['DOCKER_DIRECTORY']
        # Lancer le conteneur en arrière-plan
        print("LAUNCHING CONTAINER IN PATH : ", host_path,":",container_path)
        subprocess.run([
            "docker", "run",
            "-v", f"{host_path}:{container_path}",
            "--name", docker_config["CONTAINER_NAME"],
            "-d",
            docker_config["IMAGE_NAME"],
            "sleep", "infinity"
        ])
        print("DOCKER LAUNCHED")
