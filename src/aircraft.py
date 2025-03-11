import random

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


