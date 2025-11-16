import os
from utils import load_file, tracer


@tracer
def load_config():

    _,config_data = load_file("config/config.json")
    __,route_data = load_file("config/routes.json")
    ___,php_config = load_file("config/php_config.json")
    if _ != 200 :
        raise Exception("CAN'T FIND config.json")
    if __ != 200 :
        raise Exception("CAN'T FIND routes.json")
    if __ != 200 :
        raise Exception("CAN'T FIND php_config.json")
    config_data["DOCKER_CONFIG"]["LOCAL_PATH"] = os.path.dirname(os.path.abspath(__file__))

    return route_data, config_data, php_config