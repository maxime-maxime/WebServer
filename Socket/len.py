import pprint

lenb = {
"SCRIPT_FILENAME":[len("SCRIPT_FILENAME"),bytes([len("SCRIPT_FILENAME")])],
"/app/index.php":[len("/app/index.php"),bytes([len("/app/index.php")])],
"REQUEST_METHOD":[len("REQUEST_METHOD"), bytes([len("REQUEST_METHOD     ")])],
"GET":[len("GET"), bytes([len("GET")])],
"HTTP_HOST":[len("HTTP_HOST"),bytes([len("HTTP_HOST")])],
"localhost":[len("localhost"),bytes([len("localhost")])],
}

pprint.pp(lenb)

prm = b'\x0f\x0eSCRIPT_FILENAME/app/index.php\x0e\x03REQUEST_METHODGET\t\tHTTP_HOSTlocalhost'
