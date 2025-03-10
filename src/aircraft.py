import random

selected_aircraft = "Cessna 208 Caravan"

def get_selected_aircraft():
    return selected_aircraft

def get_aircraft_range(con, aircraft):
    cur = con.cursor()
    query = "SELECT range_km FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

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