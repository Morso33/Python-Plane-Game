#!/usr/bin/env python3
import menu
import flight_creator
import mariadb
import player
import aircraft
import osw


def main():
    print("EntryPoint called, wait for initialization")
    con = mariadb.connect(
    host='127.0.0.1',
    port=3306,
    database='flight_game',
    user='metropolia',
    password='metropolia',
    autocommit=True
    )
    print("DB con ok")
    osw.cls()
    #Set player to Helsinki-Vantaa
    gPlayer = player.cPlayer(2307, aircraft.cAircraft("medium", "Learjet 75", 860, 2, 3700), 5000)
    menu.draw(con, gPlayer)
    flight_creator.create_possible_flight(con, gPlayer)



#Call EP
if __name__ == "__main__":
    main()