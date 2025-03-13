import random

roman = ["I", "II", "III", "IV", "V", "VI"]

class Customer:
    def __init__(self, db):
        #use airport_data args: airport_id, continet
        continent = db.airport_data(db.current_airport(), "continent")
        self.name = Customer.generate_name(continent)
        self.db = db
        self.id = 0

        self.min_comfort = 1
        self.min_rp = 0
        self.deadline = 0
        self.reward   = 0
        self.reward_rp = 0
        self.accepted = 0

    def print(self):
        print("name        ", self.name)
        print("origin      ", self.origin)
        print("destination ", self.destination)
        print("reward      ", self.reward)
        print("deadline    ", self.deadline)
        print("accepted    ", self.accepted)

    def drop(self):
        cur = self.db.con.cursor()
        cur.execute("DELETE FROM customer WHERE id = ?", (self.id,))

    def gen_payout(self, distance):
        # Bit shift by tier makes payout double with each tier
        rate = 4 << (self.min_comfort-1)
        self.reward = round(distance * rate)


    def generate_tier1(self, origin_icao):
        self.origin = origin_icao
        cur = self.db.con.cursor()

        country = self.db.airport_country_icao(origin_icao)
        query = f"SELECT ident FROM airport WHERE type IN ('small_airport', 'medium_airport') AND iso_country = ? AND ident != ? ORDER BY RAND() LIMIT 1"
        cur.execute(query, (country, origin_icao,))
        result = cur.fetchone()
        self.destination = result[0]

        distance = self.db.icao_distance(origin_icao,result[0])

        self.min_comfort = random.randint(1,2)
        self.reward_rp = self.min_comfort

        self.gen_payout(distance)

    def generate_tier2(self, origin_icao):
        self.origin = origin_icao
        cur = self.db.con.cursor()
        query = f"SELECT ident FROM airport WHERE type IN ('large_airport', 'medium_airport') AND ident != ? ORDER BY RAND() LIMIT 1"
        cur.execute(query, (origin_icao,))
        result = cur.fetchone()
        self.destination = result[0]

        distance = self.db.icao_distance(origin_icao,result[0])

        self.min_comfort = random.randint(2,4)
        self.reward_rp = self.min_comfort

        self.gen_payout(distance)



    def accept(self):
        cur = self.db.con.cursor()
        query = f"UPDATE customer SET accepted = 1 WHERE id = ?"
        cur.execute(query, (self.id,))

        self.accepted = 1

    # Discard the class after saving !!!
    # Saving always creates a NEW customer
    def save(self):
        cur = self.db.con.cursor()
        query = """
            INSERT INTO customer (
                name,
                origin,
                destination,
                reward,
                reward_rp,
                deadline,
                accepted,
                min_comfort,
                min_rp
            ) VALUES (?,?,?,?,?,?,?,?,?);
        """
        cur.execute(query,
            (
                self.name,
                self.origin,
                self.destination,
                self.reward,
                self.reward_rp,
                self.deadline,
                self.accepted,
                self.min_comfort,
                self.min_rp,
            )
        )



    def load(self, customer_id):
        cur = self.db.con.cursor()
        query = """
            SELECT
                id,
                name,
                origin,
                destination,
                reward,
                reward_rp,
                deadline,
                accepted,
                min_comfort,
                min_rp
            FROM customer WHERE id = ?;
        """
        cur.execute(query, (customer_id,))
        result = cur.fetchone()

        self.id          = result[0]
        self.name        = result[1]
        self.origin      = result[2]
        self.destination = result[3]
        self.reward      = result[4]
        self.reward_rp   = result[5]
        self.deadline    = result[6]
        self.accepted    = result[7]
        self.min_comfort = result[8]
        self.min_rp      = result[9]

        self.tier = roman[self.min_comfort-1]



    def generate_name(continent: str) -> str:
        
        person_prefix = random.choice(["Mr.", "Mrs.", "Ms.", "Dr."])
        person_suffix = random.choice(["Jr.", "Sr."])

        syllables = {
            "AF": ["ba", "ka", "mo", "ntu", "za", "lo", "ngo", "ma"],
            "AS": ["shi", "ching", "ji", "wen", "li", "tan", "yu", "chong"],
            "EU": ["von", "de", "son", "ric", "ten", "dal", "mar"],
            "NA": ["ken", "win", "ton", "ada", "mex", "ver", "san"],
            "SA": ["san", "val", "rio", "gue", "bol", "ven", "per"],
            "OC": ["roo", "tas", "que", "bar", "wool", "bir", "ban"],
            "AN": ["ice", "ice", "ice", "ice", "ice", "ice", "ice"]
        }
        
        if continent not in syllables:
            print("Incorrect argument")
        
        name_parts = random.choices(syllables[continent], k=random.randint(2, 4))
        name = "".join(name_parts).capitalize()
        return f"{person_prefix} {name} {person_suffix}"
