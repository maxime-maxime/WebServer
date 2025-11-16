import threading
from load_config import load_config
from docker_manager import start_docker
from run_server import start_server
from php_config import update_php_config
from sql_server import start_mysql, stop_mysql
import os


def main():
    try :
        start_mysql()
        print("SQL SERVER LAUNCHED")
    except Exception as a :
        print("CRITICAL ERROR - SQL LAUNCHING ERROR : ",a.args)
        return

    print(os.path.dirname(os.path.abspath(__file__)))
    try :
        route_data, config_data,php_config = load_config()
    except Exception as k :
        print("CRITICAL ERROR : ", k.args)
        return

    vm_lock = threading.Lock()
    log_lock = threading.Lock()

    try:
        start_docker(config_data["DOCKER_CONFIG"], config_data["SERVER_CONFIG"]["WWW_DIRECTORY"], php_config)


        container_name = config_data['DOCKER_CONFIG']['CONTAINER_NAME']
        local_path = config_data['DOCKER_CONFIG']['LOCAL_PATH']
        update_php_config(container_name,local_path, php_config)

        try :
            start_server(config_data,route_data, vm_lock, log_lock, php_config)
        except Exception as e :
            print("CRITICAL ERROR : INTERNAL SERVER PROBLEM CAUSED IT TO CRASH :  ", e.args)
            return

    except Exception as e :
        print("CRITICAL ERROR : DOCKER CANNOT BE LAUNCHED : ",e.args)
        return


if __name__ == "__main__":
    try:
        main()
    except Exception as e :
        print("PROGRAM CLOSED : ",e.args)
    finally :
        try:
            stop_mysql()
            print("SQL Server successfully launched")
        except Exception as e:
            print("SQL CLOSING ERROR : ", e.args)
