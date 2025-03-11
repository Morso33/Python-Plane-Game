import random

selected_aircraft = "Cessna 208 Caravan"


class Aircraft:
    def __init__(self, game, aircraft_id=None):
        self.game        = game
        self.db          = game.db

        self.aircraft_id = game.aircraft_id
        if aircraft_id != None:
            self.aircraft_id = aircraft_id

        self.name      = self.get_value("name")
        self.fuel      = self.get_value("fuel")
        self.fuel_max  = self.get_value("fuel_max")
        self.speed     = self.get_value("speed_kmh")
        self.co2_kgph  = self.get_value("co2_emissions_kgph")
        self.fuel_lph  = self.get_value("fuel_consumption_lph")
        self.price     = self.get_value("price")
        self.owned     = self.get_value("owned") == 1
        self.selected  = game.aircraft_id == self.aircraft_id

        self.range_h   = (self.fuel / self.fuel_lph)
        self.range     = self.range_h * self.speed

    def get_value(self, key):
        cur = self.db.con.cursor()
        query = f"SELECT {key} FROM aircraft WHERE id = ?"
        cur.execute(query, (self.aircraft_id,))
        result = cur.fetchone()
        return result[0]

    def set_fuel(self, fuel):
        cur = self.db.con.cursor()
        query = "UPDATE aircraft SET fuel = ? WHERE id = ?"
        cur.execute(query, (fuel, self.aircraft_id,))
        self.fuel = fuel

    def purchase(self):
        cur = self.db.con.cursor()
        query = "UPDATE aircraft SET owned = 1 WHERE id = ?"
        cur.execute(query, (self.aircraft_id,))

        self.game.money -= self.price * 1000000
        self.owned     = self.get_value("owned") == 1


def get_aircraft_range(con, aircraft):
    cur = con.cursor()
    query = "SELECT range_km FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]



def get_selected_aircraft():
    return selected_aircraft


def is_aircraft_owned(con, aircraft):
    cur = con.cursor()
    query = "SELECT owned FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchall()
    if (result[0][0] == 1):
        return True
    else:
        return False

def purchase_aircraft(con, aircraft):
    cur = con.cursor()
    query = "UPDATE aircraft SET owned = 1 WHERE name = ?"
    cur.execute(query, (aircraft,))

def get_fuel_burn_per_km(con, aircraft):
    cur = con.cursor()
    query = "SELECT fuel_consumption_lph FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

def get_aircraft_type(con, aircraft):
    cur = con.cursor()
    query = "SELECT category FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

def get_payout(distance, aircraft_fuel_burn_per_km, aircraft_type):
    costs = distance * aircraft_fuel_burn_per_km
    payout = 0
    if aircraft_type == "Small":
        payout = costs * 0.25
    elif aircraft_type == "Medium":
        payout = costs * 3.5
    elif aircraft_type == "Large":
        payout = costs * 10
    else:
        pass

    payout = payout / 10

    random_factor = random.uniform(0.6, 1.6)
    rounded = round(payout * random_factor, -2)
    return int(rounded)

def calculate_flight_time(distance, aircraft_speed):
    time = distance / aircraft_speed
    time = round(time, 2)
    return time

def get_aircraft_speed(con, aircraft):
    cur = con.cursor()
    query = "SELECT speed_kmh FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

def get_aircraft_co2_emissions(con, aircraft):
    cur = con.cursor()
    query = "SELECT co2_emissions_kgph FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

def calculate_co2_emissions(flight_time_h, aircraft_co2_emissions_per_h):
    emissions = flight_time_h * aircraft_co2_emissions_per_h
    emissions = round(emissions, 2)
    return emissions
