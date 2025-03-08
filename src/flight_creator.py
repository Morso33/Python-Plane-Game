import mariadb
from geopy.distance import geodesic 
import random


def get_random_airport_id(con):
    cur = con.cursor()
    query = "SELECT id FROM airport ORDER BY RAND() LIMIT 1"
    cur.execute(query)
    return cur.fetchone()[0]

def get_lat_lon_from_airport_id(con, id):
    cur = con.cursor()
    query = "SELECT latitude_deg, longitude_deg FROM airport WHERE id=%s"
    cur.execute(query, (id,))
    return cur.fetchone()


def create_possible_flight(con):
    exit_loop = False

    while not exit_loop:
        start_airport_id = get_random_airport_id(con)

        end_airport_id = get_random_airport_id(con)

        #If the airports are the same, try again
        if start_airport_id == end_airport_id:
            continue

        #Get the coordinates of the airports
        start_airport = get_lat_lon_from_airport_id(con, start_airport_id)
        end_airport = get_lat_lon_from_airport_id(con, end_airport_id)


        #Calculate the distance between the airports
        distance = geodesic(start_airport, end_airport).km

        print("Distance between airports: " + str(distance) + " km")


