#!/bin/sh

mariadb -u metropolia --password=metropolia flight_game < ./data/lp.sql

. ./venv/bin/activate

python ./src/map.py


