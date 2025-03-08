import math
import mysql.connector

DB_CONFIG_AIRCRAFT = {
    "host": "localhost",
    "user": "root",
    "password": "Salasana",
    "database": "aircraft",
    "charset": "utf8mb4",
    "collation": "utf8mb4_general_ci"
}

DB_CONFIG_FLIGHT_GAME = {
    "host": "localhost",
    "user": "root",
    "password": "Salasana",
    "database": "flight_game",
    "charset": "utf8mb4",
    "collation": "utf8mb4_general_ci"
}

def distance(origin, destination):
    r = 6378
    lat1, lon1 = origin
    lat2, lon2 = destination

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

def aircraft_id_by(aircraft_id):
    query = "SELECT id, name, range_km, category FROM aircraft WHERE id = %s"
    with mysql.connector.connect(**DB_CONFIG_AIRCRAFT) as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(query, (aircraft_id,))  # ✅ Lisätty pilkku tuplaan
            return cursor.fetchone()

def airport_in_range(aircraft_id, origin_coords):
    aircraft = aircraft_id_by(aircraft_id)  # ✅ Käytetään oikeaa funktiota
    if not aircraft:
        print("Lentokonetta ei löytynyt.")
        return []

    range_km = aircraft["range_km"]

    query = "SELECT ident, name, type, latitude_deg, longitude_deg FROM airport"
    with mysql.connector.connect(**DB_CONFIG_FLIGHT_GAME) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute(query)
        reachable_airports = [
            {
                "ident": ap["ident"],
                "name": ap["name"],
                "type": ap["type"],
                "distance_km": round(distance(origin_coords, (ap["latitude_deg"], ap["longitude_deg"])), 2)
            }
            for ap in cursor.fetchall()
            if distance(origin_coords, (ap["latitude_deg"], ap["longitude_deg"])) <= range_km
        ]

    return sorted(reachable_airports, key=lambda x: x["distance_km"])


#Tällä voi testa!
origin = (60.3172, 24.9633)  # Helsinki-Vantaa
destination = (40.6413, -73.7781)  # JFK

distance = distance(origin, destination)
print(f"Etäisyys Helsinki-Vantaalta JFK:lle: {distance} km")
