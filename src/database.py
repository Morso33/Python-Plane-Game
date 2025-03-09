import mariadb

# Change this value to cause database to reset
SCHEMA_VERSION = "5"

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
        self.reset()


     # Write the database schema here !!!
    def reset(self):
        print("Resetting database")

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
                id          int     NOT NULL,

                name        VARCHAR(40) NOT NULL,

                origin      varchar(40),
                destination varchar(40),

                deadline    int     NOT NULL,

                PRIMARY KEY (id),

                FOREIGN KEY(origin)      REFERENCES airport(ident),
                FOREIGN KEY(destination) REFERENCES airport(ident)

            ) DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
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




    def airport_xy_icao(self, key):
        cur = self.con.cursor()
        query = "SELECT longitude_deg, latitude_deg FROM airport WHERE ident=%s"
        cur.execute(query, (key,))
        coords = cur.fetchone()
        if coords == None:
            print("Virheellinen ICAO-koodi")
            exit()
        return [coords[0],coords[1]]


