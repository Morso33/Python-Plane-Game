import mariadb
from geopy.distance import geodesic 
import random
import player


def get_random_airport_id(con, acceptable_airport_types):
    cur = con.cursor()
    placeholders = ", ".join(["%s"] * len(acceptable_airport_types))  # Create placeholder list
    query = f"SELECT id FROM airport WHERE type IN ({placeholders}) ORDER BY RAND() LIMIT 1"
    cur.execute(query, tuple(acceptable_airport_types))  # Pass values as a tuple
    result = cur.fetchone()
    return result[0]



def get_lat_lon_from_airport_id(con, id):
    cur = con.cursor()
    query = "SELECT latitude_deg, longitude_deg FROM airport WHERE id=%s"
    cur.execute(query, (id,))
    return cur.fetchone()


def create_possible_flight(con, gPlayer):
    exit_loop = False

    acceptable_airport_types = get_acceptable_airport_types_for_aircraft_type(gPlayer.current_aircraft.aircraft_type)

    while not exit_loop:

        end_airport_id = get_random_airport_id(con, acceptable_airport_types)

        #If the airports are the same, try again
        if gPlayer.current_airport_id == end_airport_id:
            continue

        #Get the coordinates of the airports
        start_airport = get_lat_lon_from_airport_id(con, gPlayer.current_airport_id)
        end_airport = get_lat_lon_from_airport_id(con, end_airport_id)

        #Calculate the distance between the airports
        distance = geodesic(start_airport, end_airport).km

        #Can the player fly that far?
        if distance > gPlayer.current_aircraft.aircraft_range:
            continue
        
        else:
            exit_loop = True
        
    return "From: " + get_airport_name_from_id(con, gPlayer.current_airport_id) + " To: " + get_airport_name_from_id(con, end_airport_id) + " Distance: " + str(distance) + " km" + " Payout: " + str(get_payout(distance, gPlayer.current_aircraft.aircraft_fuel_burn_per_km, gPlayer.current_aircraft.aircraft_type))

def get_airport_name_from_id(con, id):
    cur = con.cursor()
    query = "SELECT name FROM airport WHERE id=%s"
    cur.execute(query, (id,))
    return cur.fetchone()[0]

def get_airport_type_from_id(con, id):
    cur = con.cursor()
    query = "SELECT type FROM airport WHERE id=%s"
    cur.execute(query, (id,))
    return cur.fetchone()[0]

def get_acceptable_airport_types_for_aircraft_type(aircraft_type):
    if aircraft_type == "small":
        return ["small_airport"]
    elif aircraft_type == "medium":
        return ["medium_airport", "large_airport"]
    elif aircraft_type == "large":
        return ["large_airport"]
    else:
        pass


def get_payout(distance, aircraft_fuel_burn_per_km, aircraft_type):
    costs = distance * aircraft_fuel_burn_per_km
    payout = 0
    if aircraft_type == "small":
        payout = costs * 1.5
    elif aircraft_type == "medium":
        payout = costs * 2
    elif aircraft_type == "large":
        payout = costs * 2
    else:
        pass

    random_factor = random.uniform(0.8, 1.2)
    rounded = round(payout * random_factor, -2)
    #Remove decimals
    return int(rounded)