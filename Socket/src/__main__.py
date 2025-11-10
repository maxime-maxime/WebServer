import threading
from load_config import load_config
from docker_manager import start_docker
from run_server import start_server
from php_config import update_php_config
import os


def main():
    print(os.path.dirname(os.path.abspath(__file__)))
    route_data, config_data = load_config()
    vm_lock = threading.Lock()
    start_docker(config_data["DOCKER_CONFIG"], config_data["SERVER_CONFIG"]["WWW_DIRECTORY"])

    try :
        container_name = config_data['DOCKER_CONFIG']['CONTAINER_NAME']
        local_path = config_data['DOCKER_CONFIG']['LOCAL_PATH']
        update_php_config(container_name,local_path)
    except Exception as e :
        print(e.args)

    start_server(config_data,route_data, vm_lock)



if __name__ == "__main__":
    main()
