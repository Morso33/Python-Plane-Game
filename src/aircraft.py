import random

roman = ["I", "II", "III", "IV", "V", "VI", "VII"]

class Aircraft:
    def __init__(self, game, aircraft_id=None):
        self.game        = game
        self.db          = game.db

        self.aircraft_id = game.aircraft_id
        if aircraft_id != None:
            self.aircraft_id = aircraft_id

        self.name      = self.get_value("name")
        self.category  = self.get_value("category")
        self.fuel      = self.get_value("fuel")
        self.fuel_max  = self.get_value("fuel_max")
        self.speed     = self.get_value("speed_kmh")
        self.co2_kgph  = self.get_value("co2_emissions_kgph")
        self.fuel_lph  = self.get_value("fuel_consumption_lph")
        self.price     = self.get_value("price")
        self.comfort   = self.get_value("comfort")
        self.owned     = self.get_value("owned") == 1
        self.selected  = game.aircraft_id == self.aircraft_id

        self.has_upgrade_efficiency = self.get_value("upgrade_efficiency") == 1
        self.has_upgrade_comfort    = self.get_value("upgrade_comfort") == 1

        if self.has_upgrade_comfort:
            self.comfort += 1

        if self.has_upgrade_efficiency:
            self.fuel_lph *= 0.9
            self.co2_kgph *= 0.8

        self.range_h   = (self.fuel / self.fuel_lph)
        self.range     = self.range_h * self.speed

        self.comfort_pretty = roman[self.comfort-1]
        self.tier = self.comfort_pretty

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

        self.game.money -= self.price
        self.owned     = self.get_value("owned") == 1


    def upgrade_efficiency(self):
        cur = self.db.con.cursor()
        query = "UPDATE aircraft SET upgrade_efficiency = 1 WHERE id = ?"
        cur.execute(query, (self.aircraft_id,))
        self.has_upgrade_efficiency = self.get_value("upgrade_efficiency") == 1

    def upgrade_comfort(self):
        cur = self.db.con.cursor()
        query = "UPDATE aircraft SET upgrade_comfort = 1 WHERE id = ?"
        cur.execute(query, (self.aircraft_id,))
        self.has_upgrade_comfort    = self.get_value("upgrade_comfort") == 1

