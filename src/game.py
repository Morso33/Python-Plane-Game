import database
import random

# Temporary shit

def foobar(db):
    cur = db.con.cursor()
    query = f"SELECT ident FROM airport WHERE type = 'small_airport' AND iso_country='FI' AND ident != ? ORDER BY RAND() LIMIT 1"
    cur.execute(query, ("EFHK",))
    result = cur.fetchone()

    print(result[0])




def customers_from_airport(db, icao):
    cur = db.con.cursor()
    query = f"SELECT id FROM customer WHERE origin = ?"
    cur.execute(query, (icao,))
    result = cur.fetchall()

    customers = []

    for (customer_id,) in result:
        c = Customer(db)
        c.load(customer_id)
        customers.append(c)

    return customers;




class Customer:
    def __init__(self, db):
        self.name = f"Customer{random.randint(1, 9999)}"
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

    # Assume cessna for now
    def generate(self, origin_icao, aircraft_type="small"):
        self.origin = origin_icao
        cur = self.db.con.cursor()
        query = f"SELECT ident FROM airport WHERE type = 'small_airport' AND iso_country='FI' AND ident != ? ORDER BY RAND() LIMIT 1"
        cur.execute(query, ("EFHK",))
        result = cur.fetchone()
        self.destination = result[0]

        self.reward = 1000 * random.randint(1, 5)


    # This sucks but good enough for now (i dont care)

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

    def load(self, customer_id):
        cur = self.db.con.cursor()
        query = """
            SELECT
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

        self.name        = result[0]
        self.origin      = result[1]
        self.destination = result[2]
        self.reward      = result[3]
        self.deadline    = result[4]
        self.accepted    = result[5]

        print(result)



def main():
    db = database.Database()
    #db.reset()

    money = 5000
    airport = "EFHK"



    customers = customers_from_airport(db, airport)

    # Make sure airport has at least 3 customers
    for i in range(0, max(3 - len(customers), 0)):
        customer = Customer(db)
        customer.set_airports(airport)
        customer.save()


    customers = customers_from_airport(db, airport)
    for customer in customers:
        customer.print()




if __name__ == '__main__':
    main()
