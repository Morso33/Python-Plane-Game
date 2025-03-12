# This file has quests

from customer import Customer
from popup import Popup, impopup
from aircraft import Aircraft

tutorial_dude = "Paavo Pörssi"

class QuestManager:
    def __init__(self, game):
        self.game = game
        self.db = game.db


    def add_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("REPLACE INTO quest (flag) VALUES (?)", (flag.lower(),))

    def has_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("SELECT flag FROM quest WHERE flag = ?", (flag.lower(),))
        return len(cur.fetchall()) != 0

    def del_flag(self, flag):
        cur = self.db.con.cursor()
        cur.execute("DELETE FROM quest WHERE flag = ?", (flag.lower(),))

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
                "test_del"
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
        popup.w += 7
        popup.set_portrait("Businessman")
        popup.add_text(f"{tutorial_dude}\n")
        popup.add_text("I need an urgent flight to Soini Airfield. You can find me in the 'Look for customers' menu.")
        popup.run()

        customer = Customer(self.db)
        customer.name        = tutorial_dude
        customer.origin      = self.game.airport
        customer.destination = "FI-0008"
        customer.reward      = 3000
        customer.reward_rp   = 5
        customer.min_comfort = 1
        customer.save()


    def arrived_at_airport(self):
        self.update()
        icao = self.game.airport
        aircraft = Aircraft(self.game)

        municipality = self.db.airport_municipality(self.game.airport)


    def accepted_customer(self, customer):
        if customer.name == tutorial_dude:
            popup = Popup(self.game)
            popup.w += 7
            popup.set_portrait("Businessman")
            popup.add_text(f"{tutorial_dude}\n")
            popup.add_text("Great. Now fly me to my destination by selecting it from the map, or directly from the 'Fly to destination' menu.")
            popup.run()


    def completed_customer_flight(self, customer):
        self.update()


        if customer.name == tutorial_dude:
            popup = Popup(self.game)
            popup.w += 7
            popup.set_portrait("Businessman")
            popup.add_text(f"{tutorial_dude}\n")
            popup.add_text("Thank you! You are an excellent pilot. You will one day taxi the president of the United States, I'm sure! ")
            popup.add_text("\n")
            popup.add_text("I'll help get your new air taxi business started. You can use my hangar at Helsinki Airport to store and upgrade your aircraft.")
            popup.run()
            self.add_flag("EFHK_hangar")
            impopup(self.game, ["You have unlocked the Hangar at Helsinki Airport (EFHK)"])

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
                self.add_flag("epstein_accept")
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

        if customer.name == "Alexander Stubb":
            popup = Popup(self.game)

            popup.set_portrait(customer.name)
            popup.add_text(customer.name)
            popup.add_text("")
            popup.add_text(
                "Thank you for the great flight. I'll tell Helsinki airport staff to give you a discount on fuel and fees."
            )

            self.add_flag("efhk_discount")

            ret = popup.run()




        return True



    def spawn_stubb(self, aircraft):
        flag = "stubb_spawned"
        min_comfort = 3

        if (self.has_flag(flag)):
            return

        if aircraft.comfort < min_comfort:
            return

        customer = Customer(self.db)
        customer.name        = "Alexander Stubb"
        customer.origin      = "EFHK"
        customer.destination = "EBBR"
        customer.reward      = 20000
        customer.reward_rp   = 10
        customer.min_comfort = min_comfort
        customer.save()
        self.add_flag(flag)

    def spawn_epstein(self, aircraft):
        flag = "epstein_spawned"
        min_comfort = 4

        if (self.has_flag(flag)):
            return

        if aircraft.comfort < min_comfort:
            return

        customer = Customer(self.db)
        customer.name        = "Jeffrey Epstein"
        customer.origin      = "KJFK"
        customer.destination = "TIST"
        customer.reward      = 50000
        customer.reward_rp   = 10
        customer.min_comfort = min_comfort
        customer.save()
        self.add_flag(flag)

