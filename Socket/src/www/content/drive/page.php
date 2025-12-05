<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page 2</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>PAGE 2</h1>

</body>
</html>



<?php

if(file_exists("requetes.json")){
    $loadreq=file_get_contents("requetes.json");
    $requetesjson = json_decode($loadreq);


$servername="Localhost";
$user ="root";
$password="";

try{
    $bdd = new PDO("mysql:host=$servername;dbname=maman", $user, $password);
    $bdd -> setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); 
    echo'<p>connexion réussie</p>';
}
catch(PDOException $e){
    echo'Erreur : '.$e->getMessage();

}



$sql ='SELECT * FROM document';
$req=$bdd->query($sql);




$columnnames = [];
for ($i = 0; $i <$req->columnCount(); $i++) {
    $meta = $req->getColumnMeta($i);
    $columnnames[] = $meta['name']; 
}




echo '<form action="#" method="post">';
echo '<div class="row">';
for ($i = 0; $i < count($columnnames); $i++) {
    if($columnnames[$i]=='Chemin'){
        $chemin=$i;
    }
    else{
    echo '<div>';
    echo '<label for="text-field' . $i . '">' . $columnnames[$i] . ':</label>';
    echo '<select name="' . $i . '" id="' . $columnnames[$i] . '"><br><br>';
    $req=$bdd->query($sql);  
    echo'<option value="tout sélectionner">tout sélectionner</option>';
    $listenoir=[];
      
    while ($rep = $req->fetch()) {
        if ($rep[$i] == "0000" || $rep[$i] == "vide"){}
        elseif ($rep[$i] ==! "" && !in_array($rep[$i], $listenoir )) {
            echo'<option value="'. $rep[$i]. '">'. $rep[$i]. '</option>';   
            $listenoir[]=$rep[$i];
        }
    }
    
    echo'</select> </div>';
    if (($i + 1) % 4 == 0) {
        echo '</div><div class="row">';
    }
    }
}
echo '</div>';
echo '<input type="submit" value="Envoyer">';
echo '</form>';



if(($_SERVER['REQUEST_METHOD'] === 'POST')){
for ($i = 0; $i < count($columnnames); $i++){
    $_POST[$chemin]='tout sélectionner';
    if (isset($_POST[$i]) && $_POST[$i] !== 'tout sélectionner'){
    $form[$i] = $_POST[$i];
    $requetesjson->tab1[]=$form[$i];
    $requetesjsonencoded=json_encode($requetesjson);
    file_put_contents("requetes.json", $requetesjsonencoded);}
else{
    $form[$i] = $columnnames[$i];}
}

$instr= [];
for ($i = 0; $i < count($columnnames); $i++){
    if($form[$i] == $_POST[$i]){
        $instr[$i]= $columnnames[$i] . ' = "' . $form[$i] . '"';       
    }
    else{$instr[$i]= $columnnames[$i] . ' = '. $form[$i];
        }
}


$instr2=$instr[0] .' AND ' .$instr[1];
for ($i = 2; $i < count($columnnames); $i++){
    $instr2= $instr2. ' AND ' . $instr[$i];

}



$sql2 = 'SELECT * FROM `document` WHERE ' . $instr2 .' ORDER BY Numero_document DESC';


$req2=$bdd->query($sql2);


echo'<table><tr>';
for( $i = 0; $i<count($columnnames); $i++){
echo'<th>'. $columnnames[$i];
}

echo'</tr><tr>';

$req=$bdd->query($sql);

while($rep2=$req2->fetch()){
    echo'<tr>';
for($i = 0; $i<count($columnnames); $i++){
        $compteur=0;
        echo'<td>';
        if($rep2[$i]==0 || $rep2[$i]=='' || $rep2[$i]=='0000'){
        echo'vide';
        }
        else{
        $compteur++;
        echo $rep2[$i];
        echo'</td>';
          }
        }
    }
          echo'</tr>';
}
echo'</table>';

}

else{
    echo'le fichier json est manquant';
}

?>


