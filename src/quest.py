# This file has quests

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


