
    _
   / \   ___  ___ _ __  _ __  _   _ ___
  / _ \ / __|/ _ \ '_ \| '_ \| | | / __|
 / ___ \\__ \  __/ | | | | | | |_| \__ \
/_/   \_\___/\___|_| |_|_| |_|\__,_|___/

Seuraa ensin Tietokanta ohjeet

Asenna python3
[x] Add python.exe to PATH (onko vaadittu?)

Suorita ./setup.bat
Peli lähtee käyntiin ./run.bat


 _____ _      _        _               _
|_   _(_) ___| |_ ___ | | ____ _ _ __ | |_ __ _
  | | | |/ _ \ __/ _ \| |/ / _` | '_ \| __/ _` |
  | | | |  __/ || (_) |   < (_| | | | | || (_| |
  |_| |_|\___|\__\___/|_|\_\__,_|_| |_|\__\__,_|

Asenna MariaDB

Luo käytttäjä "metropolia" salasanalla "metropolia".
Luo tietokanta "flight_game".

Tämä onnistuu seuraavilla SQL komennoilla:

CREATE USER metropolia@localhost IDENTIFIED BY 'metropolia';
GRANT ALL PRIVILEGES ON *.* TO 'metropolia'@localhost IDENTIFIED BY 'metropolia';



DROP DATABASE flight_game;
CREATE DATABASE flight_game;
USE flight_game;
SOURCE <file>



