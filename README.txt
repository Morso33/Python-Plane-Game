         _________
         \        \
          \        \               ___    __
           \        \              \  \  / |
           /\        \              \  \/  |
         O/  \ *****  \____________  \ /   |
     \ /   ############## ***+++^^^^^^^\   \
      X **################***+++^^^^^^^ \   \
     / \   ############## ***+++^^^^^    \___\
               / \       \          \o
             O/   \       \
                   \       \
                    \       \
                     \       \
                      \_______\


		pruut pruut pöt pöt pöt pöt



 ____        _              _                   _
|  _ \  __ _| |_ __ _      | | ____ _ _ __  ___(_) ___
| | | |/ _` | __/ _` |_____| |/ / _` | '_ \/ __| |/ _ \
| |_| | (_| | || (_| |_____|   < (_| | | | \__ \ | (_) |
|____/ \__,_|\__\__,_|     |_|\_\__,_|_| |_|___/_|\___/

Kysy kaverilta zippi

 _____ _      _        _               _
|_   _(_) ___| |_ ___ | | ____ _ _ __ | |_ __ _
  | | | |/ _ \ __/ _ \| |/ / _` | '_ \| __/ _` |
  | | | |  __/ || (_) |   < (_| | | | | || (_| |
  |_| |_|\___|\__\___/|_|\_\__,_|_| |_|\__\__,_|

Asenna MariaDB 11.7

Luo käytttäjä "metropolia" salasanalla "metropolia" ja luo tietokanta "flight_game".
Tämä onnistuu seuraavilla SQL komennoilla:

CREATE USER metropolia@localhost IDENTIFIED BY 'metropolia';
GRANT ALL PRIVILEGES ON *.* TO 'metropolia'@localhost IDENTIFIED BY 'metropolia';

DROP DATABASE flight_game;
CREATE DATABASE flight_game;


./setup.bat lisää lp.sql data-kansiosta itse jos on mariadb 11.7 käytössä
jos ei niin aamuja
linuxilla ei väliä koska linux on hyvä käyttis


    _
   / \   ___  ___ _ __  _ __  _   _ ___
  / _ \ / __|/ _ \ '_ \| '_ \| | | / __|
 / ___ \\__ \  __/ | | | | | | |_| \__ \
/_/   \_\___/\___|_| |_|_| |_|\__,_|___/

Seuraa ensin Tietokanta ja data-kansio ohjeet

Asenna python3
[x] Add python.exe to PATH (onko vaadittu?)

Suorita ./setup.bat
Peli lähtee käyntiin ./run.bat



