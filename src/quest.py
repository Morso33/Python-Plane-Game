# This file has quests

from customer import Customer
from popup import Popup, impopup

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
        if not self.has_flag("quests_init"):
            flags = [
                "quests_init",
                "test_del",
                "je_new_york"
            ]

            for flag in flags:
                self.add_flag(flag)
            self.del_flag("test_del")

    def arrived_at_airport(self):
        self.update()
        icao = self.game.airport
        municipality = self.db.airport_municipality(self.game.airport)

        if self.has_flag("je_new_york") and municipality == "New York":
            self.del_flag("je_new_york")

            customer = Customer(self.db)
            customer.origin      = icao
            customer.name        = "Jeffrey Epstein"
            customer.destination = "TIST"
            customer.reward = 50000
            customer.save()

    def completed_customer_flight(self, customer):
        if customer.name == "Jeffrey Epstein":
            popup = Popup(self.game)
            popup.w = 50
            popup.add_text('        .                          ')
            popup.add_text('   ::  =::..:       Jeffrey Epstein')
            popup.add_text('  :**:.   ..-*==    ')
            popup.add_text('   -::...:::-=++:   I need trustworthy pilots')
            popup.add_text('    -:::.:::-=*+:   like yourself. Flying my')
            popup.add_text('  :=-*#%****+==+*   customers pays well, but')
            popup.add_text('  ..*@@%* %@@*%#:   you must not talk.')
            popup.add_text('  .:. ::. ==***#                   ')
            popup.add_text('  =+*-=:-=*=:=**    Want to work for me?')
            popup.add_text('   =-%..=%#-#=*.                   ')
            popup.add_text('   :=*=#*#%@%#:....                ')
            popup.add_text('   =* :=%%##*=:::::                ')
            popup.add_text(' ::+=.+:.=-+#%*=-::                ')
            popup.add_text('  :-*+*%%%%%%%*+*=-                ')
            popup.add_text('  ..--=#%%%%%#*+===                ')
            popup.add_option("Accept")
            popup.add_option("Decline")
            ret = popup.run()

            if (ret == "Accept"):
                self.add_flag("je_accept")
                customer.reward += 100000
                popup = Popup(self.game)
                popup.w = 50
                popup.add_text('        .                          ')
                popup.add_text('   ::  =::..:       Jeffrey Epstein')
                popup.add_text('  :**:.   ..-*==    ')
                popup.add_text('   -::...:::-=++:   My customers look forward')
                popup.add_text('    -:::.:::-=*+:   to flying with you. Here\'s')
                popup.add_text('  :=-*#%****+==+*   a $100k as a tip.')
                popup.add_text('  ..*@@%* %@@*%#:   ')
                popup.add_text('  .:. ::. ==***#                   ')
                popup.add_text('  =+*-=:-=*=:=**    ')
                popup.add_text('   =-%..=%#-#=*.                   ')
                popup.add_text('   :=*=#*#%@%#:....                ')
                popup.add_text('   =* :=%%##*=:::::                ')
                popup.add_text(' ::+=.+:.=-+#%*=-::                ')
                popup.add_text('  :-*+*%%%%%%%*+*=-                ')
                popup.add_text('  ..--=#%%%%%#*+===                ')
                popup.add_option("Continue")
                ret = popup.run()

            return True



        return True
