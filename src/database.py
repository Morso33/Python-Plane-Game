import mariadb
from geopy.distance import great_circle
from geopy.distance import geodesic

from customer import Customer

# Change this value to cause database to reset
SCHEMA_VERSION = "7"

class Database():
    def __init__(self):
        self.con = mariadb.connect(
            host='127.0.0.1',
            port=3306,
            database='flight_game',
            user='metropolia',
            password='metropolia',
            autocommit=True
        )

        # Reset the database if metadata is missing or schema is wrong version
        try:
            version = self.metadata_get("schema")
            if (version != SCHEMA_VERSION):
                self.reset()
        except:
            self.reset()

        # Reset anyway for now
        #self.reset()


     # Write the database schema here !!!
    def reset(self):
        #print("Resetting database")

        cur = self.con.cursor()
        cur.execute("DROP TABLE IF EXISTS metadata;")
        cur.execute("""
            CREATE TABLE metadata (
                id    VARCHAR(50) NOT NULL,
                value VARCHAR(50) NOT NULL,
                PRIMARY KEY (id)
            );
        """)

        cur.execute("DROP TABLE IF EXISTS customer;")
        cur.execute("""
            CREATE TABLE customer (
                id          int     NOT NULL AUTO_INCREMENT,

                name        VARCHAR(40) NOT NULL,

                origin      varchar(40) NOT NULL,
                destination varchar(40) NOT NULL,

                deadline    int     NOT NULL,
                reward      int     NOT NULL,
                accepted    int     NOT NULL,

                PRIMARY KEY (id),

                FOREIGN KEY(origin)      REFERENCES airport(ident),
                FOREIGN KEY(destination) REFERENCES airport(ident)

            ) DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
        """)

        cur.execute("DROP TABLE IF EXISTS quest;")
        cur.execute("""
            CREATE TABLE quest (
                flag VARCHAR(50) NOT NULL,
                PRIMARY KEY (flag)
            );
        """)

        cur.execute("DROP TABLE IF EXISTS aircraft;")
        cur.execute("""
        CREATE TABLE aircraft (
            id INT PRIMARY KEY,
            name VARCHAR(50),
            category VARCHAR(10),
            capacity INT,
            speed_kmh INT,
            range_km INT,
            fuel_tank_l INT,
            fuel_consumption_lph INT,
            co2_emissions_kgph INT,
            price_million DECIMAL(10,2)
        );""")

        cur.execute("""
        INSERT INTO aircraft (id, name, category, capacity, speed_kmh, range_km, fuel_tank_l, fuel_consumption_lph, co2_emissions_kgph, price_million) VALUES
        (1, 'Cessna 208 Caravan', 'Small', 9, 340, 1700, 1300, 220, 560, 3.00),
        (2, 'Learjet 75', 'Medium', 12, 860, 3700, 6000, 700, 1900, 5.25),
        (3, 'Boeing 747-8', 'Large', 400, 920, 14000, 240000, 12000, 30000, 250.00),
        (4, 'Boeing 747-8 VIP', 'Large', 50, 920, 14000, 240000, 12000, 30000, 250.00);
        """)

        # THIS MUST BE THE LAST LINE OF THIS FUNCTION
        self.metadata_set("schema", SCHEMA_VERSION)


    def metadata_get(self, key):
        cur = self.con.cursor()
        cur.execute("SELECT value FROM metadata WHERE id=?", (key,))
        return cur.fetchone()[0]

    def metadata_set(self, key, value):
        cur = self.con.cursor()
        cur.execute("REPLACE INTO metadata (id, value) VALUES (?, ?)", (key,value))


    def icao_exists(self, icao):
        cur = self.con.cursor()
        query = f"SELECT id FROM airport WHERE ident = ?"
        cur.execute(query, (icao,))
        result = cur.fetchall()
        if len(result) != 1:
            return False
        return True

    def icao_distance(self, icao_a, icao_b):
        a = self.airport_yx_icao(icao_a);
        b = self.airport_yx_icao(icao_b);
        return geodesic(a, b).km

    def airport_yx_icao(self, key):
        cur = self.con.cursor()
        query = "SELECT longitude_deg, latitude_deg FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        coords = cur.fetchone()
        if coords == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return [coords[1],coords[0]]

    def airport_type_icao(self, key):
        cur = self.con.cursor()
        query = "SELECT type FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        data = cur.fetchone()
        if data == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return data[0]

    def airport_country_icao(self, key):
        cur = self.con.cursor()
        query = "SELECT iso_country FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        data = cur.fetchone()
        if data == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return data[0]

    def airport_municipality(self, key):
        cur = self.con.cursor()
        query = "SELECT municipality FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        data = cur.fetchone()
        if data == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return data[0]

    def airport_xy_icao(self, key):
        cur = self.con.cursor()
        query = "SELECT longitude_deg, latitude_deg FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        coords = cur.fetchone()
        if coords == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return [coords[0],coords[1]]


    def customers_from_airport(self, icao):
        cur = self.con.cursor()
        query = f"SELECT id FROM customer WHERE origin = ?"
        cur.execute(query, (icao,))
        result = cur.fetchall()

        customers = []

        for (customer_id,) in result:
            c = Customer(self)
            c.load(customer_id)
            customers.append(c)

        return customers

    def accepted_customers(self):
        cur = self.con.cursor()
        query = f"SELECT id FROM customer WHERE accepted = 1"
        cur.execute(query, )
        result = cur.fetchall()

        customers = []

        for (customer_id,) in result:
            c = Customer(self)
            c.load(customer_id)
            customers.append(c)

        return customers
