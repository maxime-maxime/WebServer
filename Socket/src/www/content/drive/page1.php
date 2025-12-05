<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page 1</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <h1>PAGE 1</h1>

</body>

</html>



<?php




$renderTable = function (PDO $bdd, string $sql, array $columnnames): void {
    echo '<table><tr>';
    for ($i = 0; $i < count($columnnames); $i++) {
        echo '<th>' . $columnnames[$i];
    }
    echo '</tr><tr>';
    $req = $bdd->query($sql);
    while ($rep = $req->fetch()) {
        echo '<tr>';
        for ($i = 0; $i < count($columnnames); $i++) {
            $compteur = 0;
            echo '<td>';
            if ($rep[$i] == 0 || $rep[$i] == '' || $rep[$i] == '0000') {
                echo 'vide';
            } else {
                $compteur++;
                echo $rep[$i];
                echo '</td>';
            }
        }
        echo '</tr>';
    }
    echo '</table>';
};




$servername = "Localhost";
$user = "root";
$password = "";

try {
    $bdd = new PDO("mysql:host=$servername;dbname=maman", $user, $password);
    $bdd->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo '<p>connexion réussie</p>';
} catch (PDOException $e) {
    echo 'Erreur : ' . $e->getMessage();

}



$sql = 'SELECT * FROM document ORDER BY Numero_document DESC';
$req = $bdd->query($sql);





$columnnames = [];
$columntype = [];
for ($i = 0; $i < $req->columnCount(); $i++) {
    $meta = $req->getColumnMeta($i);
    $columnnames[] = $meta['name'];
    $columntype[] = $meta['native_type'];
}

for ($i = 1; $i < count($columntype); $i++) {
    echo '<br>';
    if ($columntype[$i] == 'VAR_STRING') {
        $columntype[$i] = 'type="text" maxlength="40"';
    }
    ;
    if ($columntype[$i] == 'LONG') {
        $columntype[$i] = 'type="number"';
    }
    ;
    if ($columntype[$i] == 'YEAR') {
        $columntype[$i] = 'type="number" min="1000" max="9999"';
    }
    ;
}


echo '<form action="#" method="POST" enctype="multipart/form-data">';
echo '<div class="row">';
for ($i = 1; $i < count($columnnames); $i++) {
    if ($columnnames[$i] != "Chemin") {
        echo '<div>';
        echo '<label for="text-field' . $i . '">' . $columnnames[$i] . ':</label>';
        echo '<input name="' . $i . '" id="' . $columnnames[$i] . '" ' . $columntype[$i] . ' ><br><br>';
        echo '</div>';
        if (($i + 1) % 4 == 0) {
            echo '</div><div class="row">';
        }
    } else {
        echo '<div>';
        echo '<input type="file" name="' . $i . '">';
        echo '</div>';
        $postupload = $i;
        if (($i + 1) % 4 == 0) {
            echo '</div><div class="row">';
        }

    }
}
echo '</div>';
echo '<input type="submit" value="Envoyer">';
echo '</form>';



for ($i = 1; $i <= count($columnnames); $i++) {

    if ($i == $postupload) {
        if (isset($_FILES[$i]) && $_FILES[$i]['error'] === UPLOAD_ERR_OK) {
            $fichier = $_FILES[$i];
            echo 'Fichier importé : ' . $fichier['name'] . '<br>';
            $tailleMax = 10 * 1024 * 1024;
            if ($fichier['size'] > $tailleMax) {
                echo "Fichier trop volumineux : " . $fichier['name'] . "<br>";
                exit;
            }
            //            echo "Nom temporaire du fichier : " . $fichier['tmp_name'] . '<br>';
            $chemin = 'uploads/' . $fichier['name'];
            //            echo "Chemin du fichier téléchargé : " . $chemin . '<br>';
            if (file_exists($chemin)) {
                echo 'le fichier existe deja';
                exit;
            }
            $upload = move_uploaded_file($fichier['tmp_name'], $chemin);
            if ($upload) {
                echo 'terminé';
            } else {
                echo 'erreur <br>';
            }


            $form[$postupload] = '<a href="' . $chemin . '" download="' . $fichier['name'] . '">' . $fichier['name'] . '</a>';
            //            echo'<a href="files/document.pdf" download="Document.pdf">Document.pdf</a>';





        } else {
            echo 'Aucun fichier valide pour le champ "' . $columnnames[$i] . '" <br>';
            exit;
        }
    } elseif (isset($_POST[$i]) && $_POST[$i] !== "") {
        $form[$i] = $_POST[$i];
    } else {
        $form[$i] = "vide";
    }


}
echo '<br>';

if (isset($form[$postupload])) {
    echo $form[3] . '<br><br><br><br>';
    $i = 1;
    while ($form[$i] == "vide" && $i < (count($columnnames) - 1) && $i != $postupload) {
        $i++;
    }
    if ($i == $postupload) {
        $i++;
        while ($form[$i] == "vide" && $i < (count($columnnames) - 1)) {
            $i++;
        }
    }
    if ($i < count($columnnames) - 1) {
        //print $i;
        $instr = "'" . $form[$i] . "'";
        if ($columnnames[1] == "vide") {
            $instr = "'vide'";
        } else {
            $instr = "'" . $form[1] . "'";
        }


        for ($j = 2; $j < count($columnnames); $j++) {
            if ($form[$j] == "vide") {
                $instr = $instr . ", 'vide'";
            } else {
                $instr = $instr . ",'" . $form[$j] . "'";
            }

        }



        $colonesmodif = $columnnames[1];
        for ($i = 2; $i < count($columnnames); $i++) {
            $colonesmodif = $colonesmodif . ', ' . $columnnames[$i];
        }


        $sql2 = 'INSERT INTO document (' . $colonesmodif . ') VALUES (' . $instr . ')';
        echo $sql2;

        $req2 = $bdd->query($sql2);




        $renderTable($bdd, $sql, $columnnames);
    } else {
        echo 'veuillez remplir au moins un champ';
        $effacer = unlink($chemin);
        if ($effacer) {
            echo 'le fichier ' . $fichier['name'] . ' a été effacé';
        }
    }
}
?>