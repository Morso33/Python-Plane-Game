import curses
import time
import database
from map import MapRenderer, Camera, FrameBuffer, compute_geodesic, put_gps_text
from popup import Popup, impopup
from customer import Customer
from quest import QuestManager

from geopy.distance import great_circle
from geopy.distance import geodesic

import aircraft

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

class GameState:
    def __init__(self):

        # TODO Move these two to the database
        self.money = 5000
        self.airport = "EFHK"

        self.db = database.Database()

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

        self.quests = QuestManager(self)


    def fly_to(self, icao):
        target = icao.upper()
        if not self.db.icao_exists(target):
            return

        if self.airport == target:
            return

        # Zoom out the map to at least 15deg zoom for flights
        self.cam.zoom = max(self.cam.zoom, 15)

        gps_a = self.db.airport_xy_icao(self.airport)
        gps_b = self.db.airport_xy_icao(target)

        wp = compute_geodesic(gps_a, gps_b)
        self.animate_travel(wp)

        self.airport = target
        customers = self.db.customers_from_airport(icao)

        self.quests.arrived_at_airport()

    def update_airport(self, icao):
        # Check customers at airport, generate them if necessary
        airport_type = self.db.airport_type_icao(icao)

        customers = self.db.customers_from_airport(self.airport)

        if (len(customers) > 0):
            return

        # Make sure airport has at least N customers
        customers_tier1 = 0
        customers_tier2 = 0
        match airport_type:
            case "medium_airport":
                customers_tier1 = 3
                customers_tier2 = 0
            case "large_airport":
                customers_tier1 = 2
                customers_tier2 = 3

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
        for i in range(1, len(waypoints)):

            a = waypoints[i-1]
            b = waypoints[i]

            anim_t1 = anim_t0

            distance = geodesic( (a[1],a[0]), (b[1],b[0]) ).km

            anim_dur = distance / 500.0 # km per second real-time
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
    game.update_airport(game.airport)
    customers = game.db.customers_from_airport(game.airport)
    popup = Popup(game)

    i = 0
    for customer in customers:
        i+=1
        if (customer.accepted):
            continue
        popup.add_text(f"#{i}: {customer.name}")
        distance = game.db.icao_distance(customer.origin, customer.destination)
        popup.add_text(f"{customer.origin} -> {customer.destination} ({game.db.airport_type_icao(customer.destination)})")

        popup.add_text(f"Distance: {int(distance)} km")
        popup.add_text(f"Reward:   $ {customer.reward}")
        popup.add_text(f"")
        popup.add_option(f"Board customer #{i}", i)

    popup.add_option(f"Return")
    popup.offscreen = True

    popup.postpass = customers_postpass
    popup.prepass = customers_prepass
    action = popup.run()

    if action == "Return":
        return

    customers[action-1].accept()




def menu_fly(game):
    customers = game.db.accepted_customers()
    popup = Popup(game)
    i = 0
    for customer in customers:
        i+=1
        popup.add_text(f"#{i}: {customer.name}")
        popup.add_text(f"{customer.origin} -> {customer.destination}")
        popup.add_text(f"Reward: ${customer.reward}")
        popup.add_text(f"")

        popup.add_option(f"Fly to {customer.destination}", customer.destination)

    popup.add_option(f"Choose on map")
    popup.add_option(f"Return")
    target = popup.run()

    if (target == "Choose on map"):
        target = choose_airport_from_map(game)

    game.fly_to( target )


def menu_hangar(game):
    all_aircraft = game.db.get_all_aircraft()
    popup = Popup(game)
    popup.add_text("Hangar")
    popup.add_text(f"Selected aircraft: {aircraft.selected_aircraft}")
    i = 0
    for ac in all_aircraft:
        i+=1
        #Get aircraft name
        popup.add_option(f"#{i}: {ac[1]}" + (" [Owned]" if ac[10] else ""), ac[0])
    popup.add_option("Return")
    target = popup.run()

    if target == "Return":
        return
    
    if not all_aircraft[int(target)-1][10]:
        popup = Popup(game)
        popup.add_text(f"Purchase {all_aircraft[target-1][1]} for ${all_aircraft[target-1][9]} million?")
        popup.add_option("Yes")
        popup.add_option("No")
        action = popup.run()
        if action == "Yes":

            if game.money < all_aircraft[target-1][9] * 1_000_000:
                impopup(game, ["Not enough money"], ["OK"])
            else:
                aircraft.purchase_aircraft(game.db.con, all_aircraft[target-1][1])
                impopup(game, [f"{all_aircraft[target-1][1]} purchased"], ["OK"])
    else:
        popup = Popup(game)
        popup.add_text("Select aircraft?")
        popup.add_option("Yes")
        popup.add_option("No")
        action = popup.run()
        if action == "Yes":
            aircraft.selected_aircraft = all_aircraft[target-1][1]
            impopup(game, [f"{all_aircraft[target-1][1]} selected"], ["OK"])
            #Kill all customers
            game.db.kill_all_customers()






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


        waypoints = compute_geodesic(pos, game.db.airport_xy_icao(closest_icao))
        gfx.draw_waypoints(cam, waypoints)

        gfx.fb.scanout()

        t_end = time.time()

        if (cam.zoom <= 15.0):
            draw_large_airports(gfx.fb, cam, game.db.con)

        if (cam.zoom <= 7.5):
            draw_medium_airports(gfx.fb, cam, game.db.con)

        gfx.win.addstr( gfx.fb.h//2, gfx.fb.w//2, "X" )

        gfx.win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}")
        gfx.win.addstr(2,0,f"Closest: {closest_icao}")
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



def main():
    game = GameState()

    while True:
        game.cam.gps = game.db.airport_xy_icao(game.airport)

        customers_on_board   = game.db.accepted_customers()
        for customer in customers_on_board:
            if game.airport != customer.destination:
                continue
            do_default = game.quests.completed_customer_flight(customer)
            if do_default:
                impopup(game,
                    [f"You have completed {customer.name}'s flight, and were rewarded ${customer.reward}"],
                    ["Ok"]
                )
                game.money += customer.reward
                customer.drop()

        popup = Popup(game)
        popup.add_text(f"At airport {game.airport}" )
        popup.add_text(f"Money: ${game.money}" )
        popup.add_option("Look for customers")
        popup.add_option("Fly to destination")
        popup.add_option("View your customers")
        popup.add_option("Hangar")
        popup.add_option("")
        popup.add_option("Developer options")
        popup.add_option("Quit game")
        action = popup.run()

        if action == "Developer options":
            action = impopup(game, [], [
                "Freecam",
                "Reset",
                "Fly to KJFK",
                "Quest flags",
                "Force money",
                "Return"])
            if action == "Reset":
                game.db.reset()
                impopup(game, ["Database reset"], ["Ok"])
            elif action == "Freecam":
                freecam(game)
            elif action == "Fly to KJFK":
                game.fly_to("KJFK")
            elif action == "Quest flags":
                impopup(game, game.quests.all_flags(), ["Return"])

            elif action == "Force money":
                game.money = 10_000_000
                impopup(game, ["Money set to 10 million"], ["Ok"])
                

        elif action == "Look for customers":
            menu_find_customers(game)

        elif action == "View your customers":
            pass

        elif action == "Hangar":
            menu_hangar(game)
            
            



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