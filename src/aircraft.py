#A class for all aircraft.
#Data: aircraft_type, aircraft_name, aircraft_speed, aircraft_fuel_burn_per_km, aircraft_range
class aircraft:
    def __init__(self, aircraft_type, aircraft_name, aircraft_speed, aircraft_fuel_burn_per_km, aircraft_range):
        self.aircraft_type = aircraft_type
        self.aircraft_name = aircraft_name
        self.aircraft_speed = aircraft_speed
        self.aircraft_fuel_burn_per_km = aircraft_fuel_burn_per_km
        self.aircraft_range = aircraft_range
