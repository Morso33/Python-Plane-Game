import flight_creator
import time


def fake_animation():
    print("Tanelin animaatio")
    print("Done")

    


def draw(con, gPlayer):
    print("Currently in: " + flight_creator.get_airport_name_from_id(con, gPlayer.current_airport_id) 
          + " with " + gPlayer.current_aircraft.aircraft_type + " " 
          + gPlayer.current_aircraft.aircraft_name)
    print("Money: " + str(gPlayer.money))
    
    print("Available Flights:")
    FLIGHT_COUNT = 3
    for i in range(FLIGHT_COUNT):
        flight = flight_creator.create_possible_flight(con, gPlayer)
        print(str(i + 1) + ": " + flight)
    

    print("----------------")
    print("4: Hangar")
    print("5: Exit")
    #Get user input
    user_input = input("Choose an option: ")
    if user_input == "1":
        print("Flight 1 chosen")
        fake_animation()
        draw(con, gPlayer)

    elif user_input == "2":
        print("Flight 2 chosen")
    elif user_input == "3":
        print("Flight 3 chosen")
    elif user_input == "4":
        hangar(con, gPlayer)
    elif user_input == "5":
        print("Exit")
    else:
        print("Invalid input")
        draw(con, gPlayer)




def hangar(con, gPlayer):
    print("Hangar")
    #Current aircraft
    print("Current aircraft: " + gPlayer.current_aircraft.aircraft_name)
    #View all aircraft
    print("Available aircraft:")
    cur = con.cursor()
    query = "SELECT * FROM aircraft"
    cur.execute(query)
    for row in cur:
        print(row)
    print("1: Buy aircraft")
    print("2: Exit")
    user_input = input("Choose an option: ")
    if user_input == "1":
        print("Buy aircraft")
    elif user_input == "2":
        draw(con, gPlayer)
    else:
        print("Invalid input")
        hangar(con, gPlayer)

