#!/usr/bin/env python3
import menu
import flight_creator
import mariadb
import player


def main():
    con = mariadb.connect(
    host='127.0.0.1',
    port=3306,
    database='flight_game',
    user='metropolia',
    password='metropolia',
    autocommit=True
    )
    #Set player to Helsinki-Vantaa
    player1 = player.player(3)
    print("EntryPoint called, wait for initialization")
    menu.draw()
    flight_creator.create_possible_flight(con)



#Call EP
if __name__ == "__main__":
    main()