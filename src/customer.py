import random

# This sucks but will do for now (+ i dont care)

class Customer:
    def __init__(self, db):
        self.name = f"Customer{random.randint(1000, 9999)}"
        self.db = db

        self.id = 0

        self.deadline = 0
        self.reward   = 0
        self.accepted = 0

    def print(self):
        print("name        ", self.name)
        print("origin      ", self.origin)
        print("destination ", self.destination)
        print("reward      ", self.reward)
        print("deadline    ", self.deadline)
        print("accepted    ", self.accepted)


    def summary(self):
        return f"{self.name:15} :: {self.origin:>8} -> {self.destination:8} :: ${self.reward} :: {'airport' if self.accepted==0 else 'boarded'}"



    def generate_tier1(self, origin_icao):
        exitLoop = False
        while not exitLoop:
            self.origin = origin_icao
            cur = self.db.con.cursor()
            query = f"SELECT ident FROM airport WHERE type IN ('small_airport', 'medium_airport') AND iso_country='FI' AND ident != ? ORDER BY RAND() LIMIT 1"
            cur.execute(query, ("EFHK",))
            result = cur.fetchone()
            #Calculate distance
            distance = self.db.icao_distance(origin_icao,result[0])
            if distance > 1000:
                continue


            self.destination = result[0]
            self.reward = 1000 * random.randint(1, 5)
            exitLoop = True


    def generate_tier2(self, origin_icao):
        exitLoop = False
        while not exitLoop:
            self.origin = origin_icao
            cur = self.db.con.cursor()
            query = f"SELECT ident FROM airport WHERE type IN ('large_airport', 'medium_airport') AND ident != ? ORDER BY RAND() LIMIT 1"
            cur.execute(query, ("EFHK",))
            result = cur.fetchone()

            #Calculate distance
            distance = self.db.icao_distance(origin_icao,result[0])
            if distance > 1000:
                continue

            self.destination = result[0]
            self.reward = 1000 * random.randint(1, 5)
            exitLoop = True

    def accept(self):
        cur = self.db.con.cursor()
        query = f"UPDATE customer SET accepted = 1 WHERE id = ?"
        cur.execute(query, (self.id,))

        self.accepted = 1




    def save(self):
        cur = self.db.con.cursor()
        query = """
            INSERT INTO customer (
                name,
                origin,
                destination,
                reward,
                deadline,
                accepted
            ) VALUES (?,?,?,?,?,?);
        """
        cur.execute(query,
            (
                self.name,
                self.origin,
                self.destination,
                self.reward,
                self.deadline,
                self.accepted
            )
        )


    def drop(self):
        cur = self.db.con.cursor()
        cur.execute("DELETE FROM customer WHERE id = ?", (self.id,))

    def load(self, customer_id):
        cur = self.db.con.cursor()
        query = """
            SELECT
                id,
                name,
                origin,
                destination,
                reward,
                deadline,
                accepted
            FROM customer WHERE id = ?;
        """
        cur.execute(query, (customer_id,))
        result = cur.fetchone()

        self.id          = result[0]
        self.name        = result[1]
        self.origin      = result[2]
        self.destination = result[3]
        self.reward      = result[4]
        self.deadline    = result[5]
        self.accepted    = result[6]



