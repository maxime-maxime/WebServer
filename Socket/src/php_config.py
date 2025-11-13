import Socket.src.utils as utils
from Socket.src.utils import tracer
import os

def apply_php_params(base_conf, php_params, save_path):
    lignes = base_conf.splitlines()
    lignes_modifiees = []
    for ligne in lignes:
        modifiee = False
        for param, valeur in php_params.items():
            if ligne.startswith(f"{param}="):
                if valeur == 'true' : valeur ='True'
                elif valeur == 'false' : valeur ='False'
                ligne = f"{param}={valeur}\n"
                modifiee = True
                break
        lignes_modifiees.append(ligne if modifiee else ligne + "\n")

    # Ajouter les paramètres manquants
    params_existants = [l.split('=')[0] for l in lignes_modifiees]
    for param, valeur in php_params.items():
        if param not in params_existants:
            lignes_modifiees.append(f"{param}={valeur}\n")

    # Sauvegarde du fichier
    status_save = utils.save_file(save_path, ''.join(lignes_modifiees))
    if status_save != 200:
        raise Exception(f"FAILED TO UPDATE PHP CONFIGURATIONS '{save_path}' / STATUS : {status_save}")

@tracer
def update_php_config(container_name, local_path):
    try:
        status_php, base_conf = utils.load_file("config/src/php_cgi.ini")
        status_php, base_conf_fpm = utils.load_file("config/src/php_fpm.conf")
        status_json, config_php = utils.load_file("config/php_config.json")

        if status_php != 200 or status_json != 200:
            raise Exception("FAILED TO UPDATE PHP CONFIGURATIONS STATUS : ", status_php, status_json)

        # Appliquer les paramètres CGI
        print(type(config_php[0]))
        apply_php_params(base_conf, config_php[0], "config/src/php_cgi_mod.ini")
        # Appliquer les paramètres FPM
        apply_php_params(base_conf_fpm, config_php[1], "config/src/php_pfm_mod.conf")

        _, updated_bat = utils.load_file("config/src/update_php.bat")
        if _ != 200:
            raise Exception("FAILED TO UPDATE PHP CONFIGURATIONS STATUS : ", _)
        updated_bat = updated_bat.replace("<container_name>", str(container_name))
        _ = utils.save_file("config/src/update_php.bat", updated_bat)
        if _ != 200 and _ != 201:
            raise Exception("FAILED TO UPDATE PHP CONFIGURATIONS STATUS : ", _)

        bat_path = os.path.join(local_path, r"config\src\update_php.bat").replace("\\", "/")
        ret = os.system(f'start cmd.exe /c "{bat_path}"')
        if ret != 0:
            raise Exception("FAILED TO UPDATE PHP CONFIGURATIONS")

        print("PHP CONFIG UPDATED")
    except Exception as e:
        print("WARNING : ", e.args)
        return

if __name__ == "__main__":
    update_php_config("php_5.6", "/app")
