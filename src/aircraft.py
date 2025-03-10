def get_aircraft_range(con, aircraft):
    cur = con.cursor()
    query = "SELECT range_km FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]

def is_aircraft_owned(con, aircraft):
    cur = con.cursor()
    query = "SELECT owned FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchall()
    if (result[0][0] == 1):
        return True
    else:
        return False

def purchase_aircraft(con, aircraft):
    cur = con.cursor()
    query = "UPDATE aircraft SET owned = 1 WHERE name = ?"
    cur.execute(query, (aircraft,))