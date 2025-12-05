if(file_exists("requetes.json")){
    $loadreq=file_get_contents("requetes.json");
    $requetesjson = json_decode($loadreq);
    echo $requetesjson->tab1[0];
}
else{
    echo'le fichier json est manquant';
}
