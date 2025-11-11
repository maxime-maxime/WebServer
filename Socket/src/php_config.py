import Socket.src.utils as utils
from Socket.src.utils import tracer
import os

@tracer
def update_php_config(container_name, local_path):
    try :
        # Chargement des fichiers
        status_php, base_conf = utils.load_file("config/php_cgi.ini")
        status_json, config_php = utils.load_file("config/php_config.json")

        if status_php != 200 or status_json != 200:
            raise Exception("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS")

        lignes = base_conf.splitlines()
        php_params = config_php[0]
        lignes_modifiees = []
        for ligne in lignes:
            modifiee = False
            for param, valeur in php_params.items():
                if ligne.startswith(f"{param}="):
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
        status_save = utils.save_file("config/php_cgi_mod.ini", ''.join(lignes_modifiees))
        if status_save != 200:
            raise Exception("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS")


        _,updated_bat = utils.load_file("config/update_php.bat")
        if _ != 200 :
            raise Exception("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS")
        updated_bat = updated_bat.replace("<container_name>", str(container_name))
        _ = utils.save_file("config/update_php.bat", updated_bat)
        if _ != 200 :
            raise Exception("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS")
        bat_path = os.path.join(local_path, r"config\update_php.bat")
        bat_path = bat_path.replace("\\", "/")
        ret = os.system(f'start cmd.exe /c "{bat_path}"')
        if ret != 0 :
            raise Exception("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS")
        print("PHP CONFIG UPDATED")
    except Exception as e :
        print("WARNING : FAILED TO UPDATE PHP CONFIGURATIONS : ", e.args)

if __name__ == "__main__":
    update_php_config("php_5.6", "/app")