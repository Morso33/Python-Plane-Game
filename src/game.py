import database
import random

# Jankfest game
# solo speedrunning project because group does nothing produtive

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


def accepted_customers(db):
    cur = db.con.cursor()
    query = f"SELECT id FROM customer WHERE accepted = 1"
    cur.execute(query, )
    result = cur.fetchall()

    customers = []

    for (customer_id,) in result:
        c = Customer(db)
        c.load(customer_id)
        customers.append(c)

    return customers;





class GameState:
    def __init__(self, db):
        self.db = db

        self.money = 5000
        self.airport = "EFHK"

    def fly_to(self, icao):
        target = icao.upper()

        if self.db.icao_exists(target):
            self.airport = target



def main():
    db = database.Database()
    db.reset()


    game = GameState(db)


    while True:
        print("")

        customers = customers_from_airport(db, game.airport)

        # Make sure airport has at least 3 customers
        for i in range(0, max(3 - len(customers), 0)):
            customer = Customer(db)
            customer.generate(game.airport)
            customer.save()



        customers_on_board   = accepted_customers(db)

        for customer in customers_on_board:
            if game.airport != customer.destination:
                continue
            print( f"You have completed {customer.name}'s flight, and was rewarded ${customer.reward}" )
            game.money += customer.reward
            customer.drop()

        customers_on_board   = accepted_customers(db)

        print(f"Current airport: {game.airport}")
        print(f"Money:   ${game.money}")

        customers_on_airport = customers_from_airport(db, game.airport)

        print(f"Customers on board:   {len(customers_on_board)}")
        print(f"Customers on airport: {len(customers_on_airport)}")


        for customer in customers_on_airport:
            print( customer.summary() )

        command = input("Command: ")

        argv = command.split(" ")

        match argv[0]:
            case "1":
                customers_on_airport[0].accept()
            case "2":
                customers_on_airport[1].accept()
            case "3":
                customers_on_airport[2].accept()

            # PURKKA PURKKA PURKKA
            case "fly":
                if (len(argv) == 2):
                    game.fly_to(argv[1])








if __name__ == '__main__':
    main()
