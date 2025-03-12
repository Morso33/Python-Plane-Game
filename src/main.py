import curses
import math
import time
import database
import random
from map import MapRenderer, Camera, FrameBuffer, compute_geodesic, put_gps_text
from popup import Popup, impopup
from customer import Customer
from quest import QuestManager

from geopy.distance import great_circle
from geopy.distance import geodesic

from aircraft import Aircraft
from portrait import portraits

# Engine loop architecture
#
# This game uses a rather unorthodox engine loop; hardly a loop at all but a
# stack. As the player interacts with the menus, responsibility over the
# render loop and input handling is passed from one function to another.
# A more scalable and tradinional approach would be to manage all of the
# stack-like state manually and have a large complicated central loop, but we
# don't need that complexity here.
# Arcane procedual programming techniques ;)
#




roman = ["I", "II", "III", "IV", "V", "VI"]

def create_progress_bar(progress: float, lenght: int) -> str:
    progress = max(0.0, min(100.0, progress))
    filled_lenght = int(lenght * progress)
    bar = "|" * filled_lenght + "-" * (lenght-filled_lenght)
    return bar

class GameState:
    def __init__(self):

        self.db = database.Database()
        self.load()

        # Curses initialization
        win = curses.initscr()
        curses.noecho()
        curses.cbreak()
        win.keypad(True)
        win.clear()
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        # Colors
        curses.init_pair(1, 15, 0)
        curses.init_pair(2, 9, 0)
        curses.init_pair(3, 10, 0)


        pos = self.db.airport_xy_icao("EFHK")

        fb = FrameBuffer(win)
        cam = Camera()
        cam.gps = pos.copy()
        gfx = MapRenderer(fb)

        self.cam = cam
        self.gfx = gfx
        self.win = win
        self.fb = fb

        self.status_w = 30

        self.quests = QuestManager(self)

    def load(self):
        cur = self.db.con.cursor()
        query = """
            SELECT
                airport,
                money,
                rp,
                co2,
                aircraft,
                id
            FROM game WHERE id = 1;
        """
        cur.execute(query)
        result = cur.fetchone()

        self.airport     = result[0]
        self.money       = result[1]
        self.rp          = result[2]
        self.co2         = result[3]
        self.aircraft_id = result[4]


    def save(self):
        cur = self.db.con.cursor()
        query = """
            UPDATE game SET
                airport = ?,
                money = ?,
                rp = ?,
                co2 = ?,
                aircraft = ?
            WHERE id = 1;
        """
        cur.execute(query, (
            self.airport,
            self.money,
            self.rp,
            self.co2,
            self.aircraft_id
        ))

    def status(self, row, text):
        w = self.status_w
        x = self.fb.w - w
        #x += (w - len(text))//2

        self.win.addstr(row, x, text.center(w))

    def print_status(self):
        win = self.win
        w = self.status_w
        aircraft = Aircraft(self)
        self.status(0, f"{aircraft.name} ({aircraft.tier})")
        bar = create_progress_bar( aircraft.fuel/aircraft.fuel_max, w-2)
        self.status(1, f"[{bar}]")

        km = f"{aircraft.range:.0f} km"
        rp = f"{self.rp} rp"
        co = f"{self.co2/1000:.0f} tCO²"


        w = self.status_w
        x = self.fb.w - w

        self.status(2, co)
        self.win.addstr(2, x, km)
        self.win.addstr(2, x+(w-len(rp)), rp)

        self.status(3, f"${self.money}")


    def fly_to(self, icao):
        target = icao.upper()
        if not self.db.icao_exists(target):
            return

        if self.airport == target:
            return

        airport = self.db.get_airport(icao)
        distance = self.db.icao_distance(self.airport, target)

        aircraft = Aircraft(self)


        fee_table = [0,0,0]
        match aircraft.category:
            case "Small":
                fee_table = [10, 20, 100]
            case "Medium":
                fee_table = [10, 100, 1000]
            case "Large":
                fee_table = [10, 200, 2000]


        match airport.type:
            case "small_airport":
                airport.fees = fee_table[0]
            case "medium_airport":
                airport.fees = fee_table[1]
            case "large_airport":
                airport.fees = fee_table[2]

        time = distance / aircraft.speed
        co2  = aircraft.co2_kgph * time
        fuel = aircraft.fuel_lph * time

        range_after = (aircraft.fuel - fuel) / aircraft.fuel_lph * aircraft.speed
        popup = Popup(self)
        popup.w = 60
        popup.add_text(f"Confirm flight to {icao}")
        popup.add_text(f"{airport.name}")
        popup.add_text(f"{airport.municipality}, {airport.iso_region}, {airport.continent}")
        popup.add_text(f"")
        popup.add_text(f"${self.money}, {aircraft.fuel:.1f} / {aircraft.fuel_max:.1f} l")
        popup.add_text(f"")
        popup.add_text(f"Fees:            ${airport.fees}")
        popup.add_text(f"Fuel required:   {fuel:.1f} l")
        #popup.add_text(f"Current fuel:    {aircraft.fuel:.1f} l (0%)")
        popup.add_text(f"Flight distance: {distance:.1f} km")
        popup.add_text(f"Flight time:     {time:.1f} hours")
        popup.add_text(f"CO2 emitted:     {co2:.1f} kg")
        popup.add_text(f"Spare range:     {range_after:.1f} km")
        popup.add_text(f"")
        popup.add_text(f"Airport type:    {airport.type_pretty}")
        popup.add_text(f"")
        def get_airport_description(airport_type):
            if airport_type == "small_airport":
                return "The destination is a small airport with limited services. Refueling is not available, so ensure you have enough fuel for the return journey."
            elif airport_type == "medium_airport":
                return "The destination is a medium-sized airport with basic refueling and maintenance services."
            elif airport_type == "large_airport":
                return "The destination is a large airport with full services, including refueling and maintenance."
            else:
                return "Unknown airport type. Check the airport facilities before departure."

        airport_type = "small_airport"  # Example airport type
        popup.add_text(f"{get_airport_description(airport_type)}")

        allow_depart = True

        if aircraft.fuel < fuel:
            popup.add_text(f"You do not have enough fuel to reach this destination.")
            allow_depart = False
        else:
            if airport.type == "small_airport":
                popup.add_text(f"Destination airport does not have fuel service.")

        if self.money < airport.fees:
            popup.add_text(f"You do not have enough money to cover the fees.")
            allow_depart = False


        if allow_depart == True:
            popup.add_option("Depart")

        popup.add_option("Cancel")
        ret = popup.run()
        if ret == "Cancel":
            return
        # Zoom out the map to at least 15deg zoom for flights
        self.cam.zoom = max(self.cam.zoom, 15)

        gps_a = self.db.airport_xy_icao(self.airport)
        gps_b = self.db.airport_xy_icao(target)

        wp = compute_geodesic(gps_a, gps_b)
        self.animate_travel(wp)

        self.airport = target
        self.co2 += co2
        self.money -= airport.fees
        aircraft.set_fuel(aircraft.fuel - fuel)

        # Force-generate quests ?
        customers = self.db.customers_from_airport(icao)
        self.quests.arrived_at_airport()

    def update_airport(self, icao):
        # Check customers at airport, generate them if necessary
        airport_type = self.db.airport_type_icao(icao)

        customers = self.db.customers_from_airport(self.airport)

        if (len(customers) > 0):
            return

        # Make sure airport has at least N customers
        customers_tier1 = random.randint(0,1)
        customers_tier2 = 0
        match airport_type:
            case "medium_airport":
                customers_tier1 = random.randint(1,3)
                customers_tier2 = 0
            case "large_airport":
                customers_tier1 = random.randint(1,2)
                customers_tier2 = random.randint(1,3)


        for i in range(0, customers_tier1):
            customer = Customer(self.db)
            customer.generate_tier1(icao)
            customer.save()

        for i in range(0, customers_tier2):
            customer = Customer(self.db)
            customer.generate_tier2(icao)
            customer.save()

    def animate_travel(self, waypoints):
        gfx = self.gfx
        cam = self.cam
        anim_t0 = time.time()
        aircraft = Aircraft(self)

        speed = aircraft.speed

        a = waypoints[0]
        b = waypoints[-1]
        distance = geodesic( (a[1],a[0]), (b[1],b[0]) ).km

        if (distance / speed) < 4:
            speed = distance / 4

        for i in range(1, len(waypoints)):

            a = waypoints[i-1]
            b = waypoints[i]

            anim_t1 = anim_t0

            distance = geodesic( (a[1],a[0]), (b[1],b[0]) ).km

            anim_dur = distance / speed # km per second real-time

            # Make the animation last at least N seconds

            while anim_t1 - anim_t0 < anim_dur:
                anim_t1 = time.time()
                t = (anim_t1 - anim_t0) / anim_dur
                cam.gps = [
                    a[0] + t * (b[0] - a[0]),
                    a[1] + t * (b[1] - a[1])
                ]

                wp = compute_geodesic(cam.gps, waypoints[-1])

                gfx.draw_map(cam)
                gfx.draw_waypoints(cam, wp)
                gfx.fb.scanout()
                gfx.win.refresh()
            anim_t0 = anim_t1







def customers_postpass(game):
    customers = game.db.customers_from_airport(game.airport)
    i = 0
    for customer in customers:
        i+=1
        gps = game.db.airport_xy_icao(customer.destination)
        put_gps_text(game.gfx.fb, game.cam, gps, f"● #{i}")

def customers_prepass(game):
    customers = game.db.customers_from_airport(game.airport)
    for customer in customers:
        gps = game.db.airport_xy_icao(customer.destination)
        wp = compute_geodesic(game.cam.gps, gps)
        game.gfx.draw_waypoints(game.cam, wp)


def menu_find_customers(game):
    if not game.airport:
        print("Error: No airport selected.")
        return

    game.update_airport(game.airport)

    customers = game.db.customers_from_airport(game.airport)
    if customers is None:
        print(f"Error: Failed to retrieve customers from {game.airport}.")
        return

    if not customers:
        impopup(game, ["There are no customers on this airport."])
        return

    aircraft = Aircraft(game)

    popup = Popup(game)
    i = 0
    for customer in customers:
        i += 1
        if customer.accepted:
            continue


        distance     = game.db.icao_distance(customer.origin, customer.destination)

        airport = game.db.get_airport(customer.destination)

        time = distance / aircraft.speed
        liters = aircraft.fuel_lph * time

        popup.add_text(f"#{i}: {customer.origin}: {customer.name} ({customer.tier})")

        popup.add_text(f"{airport.name}")
        popup.add_text(f"{airport.type_pretty} airport")
        popup.add_text(f"{int(distance)} km {time:.1f} h {liters:.1f} l")
        popup.add_text(f"+ ${customer.reward} {customer.reward_rp}rp")
        popup.add_text(f"")

        popup.add_option(f"Board customer #{i}", i)

    popup.add_option(f"Return")
    popup.offscreen = True
    popup.postpass = customers_postpass
    popup.prepass = customers_prepass
    action = popup.run()

    if action == "Return":
        return

    customer = customers[action-1]

    if aircraft.comfort < customer.min_comfort:
        impopup(game, [f"Comfort grade {aircraft.tier} is insufficient for a comfort grade {customer.tier} customer."])
        return

    customer.accept()




def menu_fly_postpass(game):
    customers = game.db.accepted_customers()
    i = 0
    for customer in customers:
        i+=1
        gps = game.db.airport_xy_icao(customer.destination)
        put_gps_text(game.gfx.fb, game.cam, gps, f"● {customer.destination}($)")

def menu_fly_prepass(game):
    customers = game.db.accepted_customers()
    for customer in customers:
        gps = game.db.airport_xy_icao(customer.destination)
        wp = compute_geodesic(game.cam.gps, gps)
        game.gfx.draw_waypoints(game.cam, wp)

def menu_fly(game):
    customers = game.db.accepted_customers()
    popup = Popup(game)
    i = 0
    for customer in customers:
        i+=1
        popup.add_text(f"#{i}: {customer.name}")
        popup.add_text(f"{customer.origin} -> {customer.destination}")
        popup.add_text(f"")

        popup.add_option(f"Fly to {customer.destination}", customer.destination)

    popup.add_option(f"Choose on map")
    popup.add_option(f"Return")


    popup.offscreen = True
    popup.postpass = menu_fly_postpass
    popup.prepass  = menu_fly_prepass
    target = popup.run()

    if (target == "Choose on map"):
        target = choose_airport_from_map(game)

    game.fly_to( target )


def menu_hangar(game):
    popup = Popup(game)
    popup.add_text("Hangar")

    for ac in game.db.get_all_aircraft():
        aircraft = Aircraft(game, ac[0])

        label = f"{aircraft.name:<19} | "
        price = f"${aircraft.price}"

        if aircraft.owned == True:
            price = "Owned"
        if aircraft.selected == True:
            price = "Selected"
        label += f"{price:>10}"

        popup.add_option( label, ac[0])

    popup.add_option("", -1)
    popup.add_option("Upgrades", -2)
    popup.add_option("Return", -1)

    ret = popup.run()

    if ret == -2:
        menu_upgrades(game)
        return

    if ret != -1:
        aircraft = Aircraft(game, ret)

        if aircraft.owned == False:
            if game.money < aircraft.price:
                impopup(game, ["Not enough money"], ["Ok"])
            else:
                aircraft.purchase()
                impopup(game, [f"{aircraft.name} purchased"], ["Ok"])

        if aircraft.owned == True:
            game.aircraft_id = ret






def draw_large_airports(fb, cam, con):
    try:
        cur = con.cursor()
        query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="large_airport"'
        cur.execute(query)
        for (lon, lat, ident) in cur:
            put_gps_text(fb, cam, (lon, lat), f"● {ident}")
    except Exception as e:
        print(f"Error fetching large airports: {e}")

def draw_medium_airports(fb, cam, con):
    try:
        cur = con.cursor()
        query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="medium_airport"'
        cur.execute(query)
        for (lon, lat, ident) in cur:
            put_gps_text(fb, cam, (lon, lat), f"● {ident}")
    except Exception as e:
        print(f"Error fetching medium airports: {e}")


def freecam(game):

    gfx = game.gfx
    cam = game.cam

    pos = game.db.airport_xy_icao("EFHK")
    while True:
        t_start = time.time()

        gfx.draw_map(cam)

        waypoints = compute_geodesic(pos, cam.gps)
        gfx.draw_waypoints(cam, waypoints)

        gfx.fb.scanout()

        t_end = time.time()

        if (cam.zoom <= 15.0):
            draw_large_airports(gfx.fb, cam, game.db.con)
        if (cam.zoom <= 7.5):
            draw_medium_airports(gfx.fb, cam, game.db.con)

        gfx.win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}")
        gfx.win.addstr(1,0,f"Controls: wasd to move, zx to zoom, p to toggle reprojection, Enter/l to animate travel, e to set origin")
        gfx.win.refresh()

        # Input handling
        # Python is stupid
        pan_speed = 0.1
        ch = gfx.win.getch()
        if ch == ord("q"):
            break

        elif ch == ord("a") or ch == curses.KEY_LEFT:
            cam.gps[0] -= cam.zoom * pan_speed

        elif ch == ord("d") or ch == curses.KEY_RIGHT:
            cam.gps[0] += cam.zoom * pan_speed

        elif ch == ord("w") or ch == curses.KEY_UP:
            cam.gps[1] += cam.zoom * pan_speed

        elif ch == ord("s") or ch == curses.KEY_DOWN:
            cam.gps[1] -= cam.zoom * pan_speed

        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            game.animate_travel(waypoints)
            pos = cam.gps.copy()

        elif ch == ord("l"):
            game.animate_travel(waypoints)

        elif ch == ord("e"):
            pos[0] = cam.gps[0]
            pos[1] = cam.gps[1]

        elif ch == ord("z"):
            cam.zoom *= 2.0

        elif ch == ord("x"):
            cam.zoom *= 0.5


def choose_airport_from_map(game):

    gfx = game.gfx
    cam = game.cam

    pos = game.db.airport_xy_icao(game.airport)
    while True:
        t_start = time.time()

        gfx.draw_map(cam)

        closest_icao = game.airport
        closest_distance = float('inf')
        if True:
            cur = game.db.con.cursor()
            query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="large_airport"'
            if (cam.zoom <= 7.5):
                query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type IN ("medium_airport", "large_airport")'
            cur.execute(query)



            for (lon, lat, ident) in cur:
                put_gps_text(game.gfx.fb, cam, (lon,lat), f"● {ident}")
                # Square root not necessary, we don't need the true distance,
                # only relative.
                distance = (lon - cam.gps[0])**2 + (lat - cam.gps[1])**2
                if (closest_distance > distance):
                    closest_distance = distance
                    closest_icao = ident

            customers = game.db.accepted_customers()
            for customer in customers:
                ident = customer.destination
                gps = game.db.airport_xy_icao(ident)
                lon = gps[0]
                lat = gps[1]
                distance = (lon - cam.gps[0])**2 + (lat - cam.gps[1])**2
                if (closest_distance > distance):
                    closest_distance = distance
                    closest_icao = ident




        waypoints = compute_geodesic(pos, game.db.airport_xy_icao(closest_icao))
        gfx.draw_waypoints(cam, waypoints)

        gfx.fb.scanout()

        menu_fly_postpass(game)
        game.print_status()

        if (cam.zoom <= 15.0):
            draw_large_airports(gfx.fb, cam, game.db.con)

        if (cam.zoom <= 7.5):
            draw_medium_airports(gfx.fb, cam, game.db.con)

        distance = game.db.icao_distance(game.airport, closest_icao)
        distance_text = f"{distance:.0f} km"
        gfx.win.addstr( gfx.fb.h//2,   gfx.fb.w//2, "X" )
        gfx.win.addstr( gfx.fb.h//2+1, gfx.fb.w//2- len(distance_text)//2, distance_text )

        t_end = time.time()

        gfx.win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}")
        gfx.win.addstr(2,0,f"Target: {closest_icao}")
        gfx.win.refresh()

        # Input handling
        # Python is stupid
        pan_speed = 0.075
        ch = gfx.win.getch()
        if ch == ord("q"):
            return ""

        elif ch == ord("a") or ch == curses.KEY_LEFT:
            cam.gps[0] -= cam.zoom * pan_speed

        elif ch == ord("d") or ch == curses.KEY_RIGHT:
            cam.gps[0] += cam.zoom * pan_speed

        elif ch == ord("w") or ch == curses.KEY_UP:
            cam.gps[1] += cam.zoom * pan_speed

        elif ch == ord("s") or ch == curses.KEY_DOWN:
            cam.gps[1] -= cam.zoom * pan_speed

        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            return closest_icao

        elif ch == ord("z"):
            cam.zoom *= 2.0

        elif ch == ord("x"):
            cam.zoom *= 0.5


def menu_game_start(game):
    popup = Popup(game)
    if game.quests.has_flag("game_start"):
        popup.add_option("Continue")

    popup.add_option("New Game")
    ret = popup.run()
    if ret == "New Game":
        game.db.reset()


def menu_upgrades(game):
    while True:
        popup = Popup(game)
        aircraft = Aircraft(game)
        popup.w = 70
        # Calculate these based on aircraft type
        comfort_cost    = 0
        efficiency_cost = 0
        match aircraft.category:
            case "Small":
                comfort_cost    = 10000
                efficiency_cost = 10000
            case "Medium":
                comfort_cost    = 20000
                efficiency_cost = 20000
            case "Large":
                comfort_cost    = 50000
                efficiency_cost = 50000


        new_tier = roman[aircraft.comfort] # +1 but because 0-index -1 so 0

        price_label = "Purchased" if aircraft.has_upgrade_comfort  else f"${comfort_cost}"
        popup.add_text(f"Comfort Upgrade      {price_label}")
        popup.add_text(f"Increases the comfort rating of your aircraft by one.")
        popup.add_text("")

        price_label = "Purchased" if aircraft.has_upgrade_efficiency  else f"${efficiency_cost}"
        popup.add_text(f"Efficiency Upgrade   {price_label}")
        popup.add_text(f"Reduces fuel consumption by -10% and CO² emissions by -20%.")

        if not aircraft.has_upgrade_comfort and game.money >= comfort_cost:
            popup.add_option(f"Upgrade comfort",   1)
        if not aircraft.has_upgrade_efficiency and game.money >= efficiency_cost:
            popup.add_option(f"Upgrade efficiency",2)

        popup.add_option(f"Return",0)

        ret = popup.run()

        if ret == 1:
            aircraft.upgrade_comfort()
        elif ret == 2:
            aircraft.upgrade_efficiency()
        else:
            break



def menu_refuel(game):
    aircraft = Aircraft(game)

    if (aircraft.fuel == aircraft.fuel_max):
        impopup(game, ["Your tanks are full."])
        return

    popup = Popup(game)

    price_per_liter = 1.1

    fuel_can_afford = game.money / price_per_liter
    fuel = aircraft.fuel_max - aircraft.fuel

    price = fuel * price_per_liter

    price = math.ceil(price)

    popup.add_text(f"Money:       ${game.money}")
    popup.add_text(f"Fuel:        {aircraft.fuel:.1f} / {aircraft.fuel_max:.1f} liters")
    popup.add_text(f"Fuel price:  ${price_per_liter} / liter")

    popup.add_option(f"Buy {fuel:.1f} liters for ${price}", "buy")
    popup.add_option("Return")

    ret = popup.run()

    if ret == "buy":
        game.money -= price
        aircraft.set_fuel( aircraft.fuel + fuel )
        impopup(game, ["Aircraft refueled."])


def main():
    game = GameState()

    menu_game_start(game)

    game.load()

    while True:
        game.cam.gps = game.db.airport_xy_icao(game.airport)
        game.quests.update()

        aircraft = Aircraft(game)

        customers_on_board   = game.db.accepted_customers()
        for customer in customers_on_board:
            if game.airport != customer.destination:
                continue
            do_default = game.quests.completed_customer_flight(customer)
            if do_default:
                popup = Popup(game)
                popup.w = 60
                popup.add_text(f"You have completed {customer.name}'s flight.\n")
                popup.add_text(f"+ ${customer.reward}")
                popup.add_text(f"+ {customer.reward_rp} rp")
                popup.run()
                game.money += customer.reward
                game.rp    += customer.reward_rp
                customer.drop()

        game.save()
        popup = Popup(game)
        popup.w = 60
        airport = game.db.get_airport(game.airport)
        popup.add_text(f"At airport {airport.ident} - {airport.name}" )
        popup.add_text(f"{airport.municipality} ({airport.continent} {airport.iso_region})" )
        popup.add_text(f"{airport.type_pretty} airport" )
        popup.add_text(f"" )
        popup.add_text(f"Money:              ${game.money}" )
        popup.add_text(f"CO² emissions:      {game.co2:0.0f} kg" )
        popup.add_text(f"Reputation:         {game.rp} rp" )
        popup.add_text(f"" )
        popup.add_text(f"Aircraft:           {aircraft.name}" )
        popup.add_text(f"Fuel:               {aircraft.fuel:0.1f} / {aircraft.fuel_max:0.1f} liters" )
        popup.add_text(f"Range:              {aircraft.range:0.1f} km" )
        popup.add_text(f"Comfort class:      {aircraft.comfort_pretty}" )
        popup.add_text(f"")
        popup.add_option("Look for customers")
        popup.add_option("Fly to destination")
        #popup.add_option("View your customers") TODO ?

        if airport.type != "small_airport":
            popup.add_option("Refuel")
        if airport.ident == "EFHK":
            popup.add_option("")
            popup.add_option("Hangar")
            popup.add_option("Upgrades")

        popup.add_option("")
        popup.add_option("Developer options")
        popup.add_option("Quit game")
        action = popup.run()

        if action == "Developer options":
            while True:
                action = impopup(game, [], [
                    "Freecam",
                    "Reset",
                    "Quest flags",
                    "+ $10,000,000",
                    "+ $100,000,000",
                    "Become opiskelija",
                    "Fly to New York",
                    "View portraits",
                    "",
                    "Return"])
                if action == "Reset":
                    game.db.reset()
                    game.load()
                    impopup(game, ["Database reset"], ["Ok"])
                    break
                elif action == "Freecam":
                    freecam(game)
                elif action == "Fly to New York":
                    game.fly_to("KJFK")
                    break
                elif action == "Quest flags":
                    impopup(game, game.quests.all_flags(), ["Return"])
                elif action == "Become opiskelija":
                    game.money = 0
                    impopup(game, ["You are now broke."])
                    break

                elif action == "View portraits":
                    while True:
                        who = impopup(game, [], portraits.keys())
                        if who == "Return":
                            break
                        popup = Popup(game)
                        popup.set_portrait(who)
                        popup.add_text(f"{who}")
                        popup.run()
                    break
                elif action == "+ $10,000,000":
                    game.money += 10_000_000
                    impopup(game, ["$10 million added"], ["Ok"])

                elif action == "+ $100,000,000":
                    game.money += 100_000_000
                    impopup(game, ["$100 million added"], ["Ok"])
                else:
                    break


        elif action == "Look for customers":
            menu_find_customers(game)
        elif action == "View your customers":
            pass
        elif action == "Hangar":
            menu_hangar(game)
        elif action == "Refuel":
            menu_refuel(game)
        elif action == "Upgrades":
            menu_upgrades(game)
        elif action == "Fly to destination":
            menu_fly(game)

        elif action == "Quit game":
            impopup(game, [], ["Bye bye !"])
            break

    game.win.keypad(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()


if __name__ == "__main__":
    main()
