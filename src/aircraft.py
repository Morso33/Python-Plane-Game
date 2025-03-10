def get_aircraft_range(con, aircraft):
    cur = con.cursor()
    query = "SELECT range_km FROM aircraft WHERE name = ?"
    cur.execute(query, (aircraft,))
    result = cur.fetchone()
    return result[0]