# This file has quests

from customer import Customer
from popup import Popup, impopup
from aircraft import Aircraft

class QuestManager:
    def __init__(self, game):
        self.game = game
        self.db = game.db


    def add_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("REPLACE INTO quest (flag) VALUES (?)", (flag,))

    def has_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("SELECT flag FROM quest WHERE flag = ?", (flag,))
        return len(cur.fetchall()) != 0

    def del_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("DELETE FROM quest WHERE flag = ?", (flag,))

    def all_flags(self):
        cur = self.db.con.cursor()
        cur.execute("SELECT flag FROM quest")
        ret = []
        for row in cur.fetchall():
            ret.append(row[0])
        return ret

    def update(self):
        if not self.has_flag("game_start"):
            flags = [
                "game_start",
                "test_del",
                "je_new_york"
            ]

            for flag in flags:
                self.add_flag(flag)
            self.del_flag("test_del")

            self.tutorial_quest()

        aircraft = Aircraft(self.game)
        self.spawn_stubb(aircraft)
        self.spawn_epstein(aircraft)

    def tutorial_quest(self):
        popup = Popup(self.game)
        popup.add_text("Welcome! This is a placeholder for tutorial quest.")
        popup.add_option("Continue")
        popup.run()

    def arrived_at_airport(self):
        self.update()
        icao = self.game.airport
        aircraft = Aircraft(self.game)

        municipality = self.db.airport_municipality(self.game.airport)



    def completed_customer_flight(self, customer):
        self.update()
        if customer.name == "Jeffrey Epstein":
            popup = Popup(self.game)

            popup.set_portrait(customer.name)
            popup.add_text(customer.name)
            popup.add_text("")
            popup.add_text(
                "I need trustworthy pilots like yourself. Flying my "+
                "customers pays well, but you must not talk. \n\n"+
                "Want to work for me?"
            )

            popup.add_option("Accept")
            popup.add_option("Decline")
            ret = popup.run()

            if (ret == "Accept"):
                self.add_flag("je_accept")
                customer.reward += 100000
                popup = Popup(self.game)
                popup.set_portrait(customer.name)
                popup.add_text(customer.name)
                popup.add_text("")
                popup.add_text(
                    "Excellent! My customers look forward to flying with "+
                    "you. Here's a $100k tip."
                )

                ret = popup.run()

            return True



    def spawn_stubb(self, aircraft):
        flag = "stubb_spawned"
        if (self.has_flag(flag)):
            return

        if aircraft.comfort < 3:
            return

        customer = Customer(self.db)
        customer.name        = "Alexander Stubb"
        customer.origin      = "EFHK"
        customer.destination = "EBBR"
        customer.reward      = 20000
        customer.reward_rp   = 10
        customer.min_comfort = 3
        customer.save()
        self.add_flag(flag)

    def spawn_epstein(self, aircraft):
        flag = "epstein_spawned"
        if (self.has_flag(flag)):
            return

        if aircraft.comfort < 3:
            return

        customer = Customer(self.db)
        customer.name        = "Jeffrey Epstein"
        customer.origin      = "KJFK"
        customer.destination = "TIST"
        customer.reward      = 50000
        customer.reward_rp   = 10
        customer.min_comfort = 3
        customer.save()
        self.add_flag(flag)

