#!/usr/bin/env python3
import database
import textwrap
import shapefile
import array
import math
import time
import curses
from geopy.distance import great_circle
from geopy.distance import geodesic

from customer import Customer
from popup import Popup

# Coordinate systems

# Clip space / Normalized device coordinates
# Term borrowed from computer graphics. Represents normalized screen
# coordinates. Float in range 0.0-1.0 for both x and y in this application.
# Origin [0, 0] in top left corner of display.
# Note: 1.0 is actually clipped off, but 0.0 isn't.
#
#          +x ->
#    0,0 __________ 1,0
#       |          |
# +y    |  screen  |
#  |    |          |
#  v    |__________|
#    0,1            1,1
#
# To convert GPS coordinates to clip space, use cam.project_gps()


# GPS: longitude (x), latitude (y)
# This is the coordinate system used as our 2d projection of earth. Do note
# it's grossly distorted from world space, eg distances cannot be calculated
# using this. Mainly used just for rendering logic.
# In degrees. Note: math functions typically require radians.
# Always use (longitude, latitude) order when grouping coordinates. X before Y.
# Library functions like geopy may require opposite order, pay attention. Wrap
# such functions if possible.
# Fun fact: GPS coordinates are functionally equilevelant to yaw and pitch.
#
#    longitude(x)
# -180    0     180
#   _____________
#  |_|_|_|_|_|_|_|  90
#  |_|_|_GMT_|_|_|
#  |_|_|_|_|_|_|_|  0   latitude(y)
#  |_|_|_|_|_|_|_|
#  |_|_|_|_|_|_|_| -90
#

# Mercator:
# Same as GPS, but using the Mercator projection. Stretches the map near poles
# to match common mapping programs. Only used as alternative projection in
# rendering.
# https://en.wikipedia.org/wiki/Mercator_projection
#
#         x
# -180    0     180
#   _____________
#  | | | | | | | |
#  | | | | | | | |
#  |_|_|_|_|_|_|_|
#  | | | | | | | |
#  |_|_|_|_|_|_|_|
#  |_|_|_|_|_|_|_|  0 y
#  | | | | | | | |
#  |_|_|_|_|_|_|_|
#  | | | | | | | |
#  | | | | | | | |
#  |_|_|_|_|_|_|_|
#
# gps_to_mercator()


# Unit sphere
# Normalized XYZ vector. Origin is center of earth, with earth's
# radius = 1.0, and diameter = 2.0. Earth is a perfect sphere in this model.
# If ~realistic distances are to be calculated, simply multiply this vector by
# earth's true radius.
# Every 3d vector of lenght 1.0 can be mapped to a GPS coordinate and back.
#
#                    X
#         -1.0______0.0______1.0
#                  _____
#    1.0 |      .-'.  ':'-.
#        |    .''::: .:    '.
#        |   /   :::::'      \
#        |  ;.    ':' `       :
#  Y 0.0 |  |       '..       |
#        |  : '      ::::.    ;
#        |   \       '::::   /
#        |    '.      :::  .'<--- [ 0.71, -0.71 ]
#   -1.0 |      '-.___'_.-'
#
#
# Functions to convert between usphere and gps coordinates:
# gps_to_usphere()
# usphere_to_gps()

# Character palette used for rendering
#lut = (" ","▘","▝","▀","▖","▌","▞","▛","▗","▚","▐","▜","▄","▙","▟","█");
lut = (" ","`","'","\"",",",":","/","F",".","\\",":","\\","_","b","d","-");


def gps_to_usphere(gps_deg):
    gps = ( math.radians(gps_deg[0]-90), math.radians(gps_deg[1]) )
    xz = math.cos(gps[1])
    x = xz * math.cos(gps[0])
    y = math.sin(gps[1])
    z = xz * math.sin(-gps[0])
    return [x,y,z]

def usphere_to_gps(vec):
    lat = math.asin(vec[1])
    lon = math.atan2(vec[0], vec[2])
    return [math.degrees(lon), math.degrees(lat)]

disable_mercator = False
def gps_to_mercator(gps):
    if (disable_mercator):
        return gps
    w = 360
    h = 180
    x = gps[0]

    lat = math.radians( max(min(gps[1], 87), -87)  )

    mercN = math.log( math.tan( (math.pi/4) + (lat/2)) )
    y = (w * mercN/(2*math.pi))

    return [x,y]





def vec3_lenght(vec):
    return math.sqrt( vec[0]*vec[0] + vec[1]*vec[1] + vec[2]*vec[2] );

def vec3_normalize(vec):
    lenght = vec3_lenght(vec)
    vec[0] /= lenght
    vec[1] /= lenght
    vec[2] /= lenght






def draw_large_airports(fb, cam, con):
    cur = con.cursor()
    query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="large_airport"'
    cur.execute(query)
    for (lon, lat, ident) in cur:
        put_gps_text(fb, cam, (lon,lat), f"● {ident}")

def draw_medium_airports(fb, cam, con):
    cur = con.cursor()
    query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="medium_airport"'
    cur.execute(query)
    for (lon, lat, ident) in cur:
        put_gps_text(fb, cam, (lon,lat), f"○ {ident}")

def draw_small_airports(fb, cam, con):
    cur = con.cursor()
    query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="small_airport"'
    cur.execute(query)
    for (lon, lat, ident) in cur:
        put_gps_text(fb, cam, (lon,lat), f"s● {ident}")

def icao_coords(con, key):
    cur = con.cursor()
    query = "SELECT longitude_deg, latitude_deg FROM airport WHERE ident=%s"
    cur.execute(query, (key,))
    coords = cur.fetchone()
    if coords == None:
        print("Virheellinen ICAO-koodi")
        exit()
    return [coords[0],coords[1]]





# "In geometry, a geodesic is a curve representing the locally
# shortest path (arc) between two points in a surface" - Wikipedia
# This is ultimately just a bad sphere lerp

def compute_geodesic(gps_a, gps_b):
    waypoints = []

    a = gps_to_usphere(gps_a)
    b = gps_to_usphere(gps_b)

    # Resolution of geodesic
    steps = 15

    for step in range(0, steps+1):
        t = (step/steps);

        # Interpolate between two vectors
        c = [
            a[0] + t * (b[0] - a[0]),
            a[1] + t * (b[1] - a[1]),
            a[2] + t * (b[2] - a[2]),
        ]

        vec3_normalize(c)
        gps = usphere_to_gps(c)

        waypoints.append(gps)
    return waypoints




# Writing text to buffer must be done *after* map scanout
def put_gps_text(fb, cam, gps, text):
    label = cam.project_gps(gps)
    x = int(label[0] * fb.w)
    y = int(label[1] * fb.h)
    if not (x < 0 or y < 0 or x >= fb.w or y >= fb.h):
        fb.win.addstr( y, x, text )



# This is the buffer from which ascii graphics are ultimately generated
# Each pixel gets a 32bit value; last 4 bits are "subpixels", other bits
# determine color and such
class FrameBuffer:
    def __init__(self, win):
        self.w = 300
        self.h = 80
        self.buffer = []
        self.win = win
        self.update()

    def update(self):
        maxyx = self.win.getmaxyx()
        self.h = maxyx[0]-1
        self.w = maxyx[1]-1

    def clear(self):
        self.update()
        required_len = self.w * self.h
        if (len(self.buffer) != required_len):
            self.buffer =  array.array('i', ([0]*(required_len)))

    def pixel(self, clip):
        pixel = (clip[0] * self.w, clip[1] * self.h)
        self.write_subpixel(pixel)

    def write_subpixel(self, pixel, data=0):

        if (pixel[0] > self.w-1 or pixel[1] > self.h-1):
            return

        if (pixel[0] < 0 or pixel[1] < 0):
            return

        subpixel = (pixel[0]%1, pixel[1]%1)
        val = 1;
        if subpixel[0] >= 0.5:
            val <<= 1
        if subpixel[1] >= 0.5:
            val <<= 2
        pxl = self.buffer[ int(pixel[1])*self.w + int(pixel[0]) ];
        pxl = pxl|val | (pxl&0xF|(data<<8))
        self.buffer[ int(pixel[1])*self.w + int(pixel[0]) ] = pxl;

    # Common DDA line drawing algorithm
    def line(self, clip_a, clip_b, data=0):
        a = (clip_a[0] * (self.w*2), clip_a[1] * (self.h*2))
        b = (clip_b[0] * (self.w*2), clip_b[1] * (self.h*2))

        dx = int(b[0] - a[0])
        dy = int(b[1] - a[1])

        steps = max(abs(dx), abs(dy))
        if (steps == 0):
            return
        xinc = dx/steps
        yinc = dy/steps

        x = a[0]
        y = a[1]

        for i in range(steps+1):
            self.write_subpixel((x*0.5,y*0.5), data)
            x += xinc
            y += yinc
        self.write_subpixel((a[0]*0.5,a[1]*0.5), data)
        self.write_subpixel((b[0]*0.5,b[1]*0.5), data)

    def scanout(self):
        for x in range(self.w):
            for y in range(self.h):
                index = y * self.w + x
                char = self.buffer[index]
                block = char & 0xFF
                match block:
                    case 0:
                        self.win.addch(y, x, " ", curses.color_pair(0))
                    case _:
                        self.win.addch(y, x, lut[block], curses.color_pair( (char>>8)+1) )
                self.buffer[index] = 0


class Camera:
    def __init__(self):
        self.gps = [0, 0]
        self.zoom = 30;
        self.bbox = [0,0,0,0]
        self.aspect = 1.0

    # Converts GPS to clip space
    def project_gps(self, gps):
        x = gps[0]
        y = gps[1]
        x,y = gps_to_mercator(gps)
        point = [
               (x - self.offset[0])/self.scale[0],
           1.0-(y - self.offset[1])/self.scale[1],
        ]
        return point

    def update_clip(self, fb):
        self.aspect = fb.w / fb.h / 2.0

        x,y = gps_to_mercator(self.gps)

        bbox = [
            x - self.zoom * self.aspect, y - self.zoom,
            x + self.zoom * self.aspect, y + self.zoom,
        ]

        self.scale  = [(bbox[2] - bbox[0]), (bbox[3] - bbox[1])]
        self.offset = [bbox[0], bbox[1]]
        self.bbox = bbox;


class MapRenderer:
    def __init__(self, fb):
        self.fb = fb
        self.win = fb.win

        # Load map data
        self.sf_low  = shapefile.Reader("./data/ne_110m_admin_0_countries/ne_110m_admin_0_countries")
        #self.sf_mid  = shapefile.Reader("./data/ne_50m_admin_0_countries/ne_50m_admin_0_countries")
        #sf_high = shapefile.Reader("./data/ne_10m_admin_0_countries/ne_10m_admin_0_countries")

    def draw_map(self, cam):
        sf = self.sf_low
        fb = self.fb

        #if (cam.zoom < 15.0):
        #    sf = sf_mid
        #if (cam.zoom < 0.5):
        #    sf = sf_high

        shapes = sf.shapes()

        fb.clear()
        cam.update_clip(fb)

        for shape in shapes:

            shape.parts.append(len(shape.points))

            bmin = gps_to_mercator((shape.bbox[0], shape.bbox[1]))
            bmax = gps_to_mercator((shape.bbox[2], shape.bbox[3]))

            # AABB culling
            if (bmax[0] < cam.bbox[0]) or (bmin[0] > cam.bbox[2]) :
                continue
            if (bmax[1] < cam.bbox[1]) or (bmin[1] > cam.bbox[3]) :
                continue


            for j in range(1, len(shape.parts)):
                for i in range(shape.parts[j-1]+1, shape.parts[j]):
                    point = shape.points[i]

                    vertex_a = cam.project_gps(point)

                    point = shape.points[i-1]
                    vertex_b = cam.project_gps(point)

                    linebbox = (
                        min(vertex_a[0], vertex_b[0]), min(vertex_a[1], vertex_b[1]),
                        max(vertex_a[0], vertex_b[0]), max(vertex_a[1], vertex_b[1]),
                    )

                    # Cull individual lines
                    if (linebbox[2] < 0.0) or (linebbox[0] > 1.0) :
                        continue
                    if (linebbox[3] < 0.0) or (linebbox[1] > 1.0) :
                        continue

                    fb.line(vertex_a, vertex_b)
                    #fb.pixel(vertex_a)
                    fb.pixel(vertex_b)

    def draw_gamestate(self, game):
        x = self.fb.w - 40;
        self.win.addstr(0, x, f"Current airport: {game.airport}" )
        self.win.addstr(1, x, f"${game.money}" )



    def draw_waypoints(self, cam, waypoints):
        last = cam.project_gps(waypoints[0])
        for i in range(1, len(waypoints)):
            cur = cam.project_gps(waypoints[i])
            self.fb.line(last, cur, 1)
            last = cur



def animate_travel(gfx, cam, waypoints):
    anim_t0 = time.time()
    for i in range(1, len(waypoints)):

        a = waypoints[i-1]
        b = waypoints[i]

        anim_t1 = anim_t0

        distance = geodesic( (a[1],a[0]), (b[1],b[0]) ).km

        anim_dur = distance / 1000.0
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




def impopup(game, text, options):
    popup = Popup(game)

    for line in text:
        popup.add_text(line)

    for line in options:
        popup.add_option(line)

    return popup.run()




def freecam(game):

    gfx = game.gfx
    cam = game.cam

    pos = game.db.airport_xy_icao("EFHK")
    while True:
        t_start = time.time()

        gfx.draw_map(cam)

        #for x in range(-180, 180, 60):
        #    fb.line( cam.project_gps((x,-90)), cam.project_gps((x,90)), 2)
        #for y in range(-180, 180-10, 60):
        #    fb.line( cam.project_gps((-180, y)), cam.project_gps((180, y)), 2)

        waypoints = compute_geodesic(pos, cam.gps)
        gfx.draw_waypoints(cam, waypoints)

        gfx.fb.scanout()

        #gfx.draw_gamestate(game)

        t_end = time.time()

        if (cam.zoom <= 15.0):
            draw_large_airports(gfx.fb, cam, game.db.con)
        #if (cam.zoom <= 3.75):
        if (cam.zoom <= 7.5):
            draw_medium_airports(gfx.fb, cam, game.db.con)
        #if (cam.zoom <= 1.00):
        #    draw_small_airports(gfx.fb, cam, game.db.con)
        #put_gps_text(fb, cam, airport_a, "EFHK")

        gfx.win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}")
        #gfx.win.addstr(1,0,f"Controls: wasd to move, zx to zoom, p to toggle reprojection, Enter to animate travel")
        #gfx.win.addstr(2,0,f"{pos}")
        #win.addstr(2,0,f"Distance: { geodesic( (airport_a[1],airport_a[0]), (cam.gps[1],cam.gps[0]) ).km }")
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
            animate_travel(gfx, cam, waypoints)
            pos = cam.gps.copy()

        elif ch == ord("l"):
            animate_travel(gfx, cam, waypoints)

        elif ch == ord("e"):
            pos[0] = cam.gps[0]
            pos[1] = cam.gps[1]

        elif ch == ord("z"):
            cam.zoom *= 2.0

        elif ch == ord("x"):
            cam.zoom *= 0.5

        elif ch == ord("p"):
            global disable_mercator
            disable_mercator = not disable_mercator


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

        #gfx.draw_gamestate(game)

        t_end = time.time()

        if (cam.zoom <= 15.0):
            draw_large_airports(gfx.fb, cam, game.db.con)
        #if (cam.zoom <= 3.75):
        if (cam.zoom <= 7.5):
            draw_medium_airports(gfx.fb, cam, game.db.con)
        #if (cam.zoom <= 1.00):
        #    draw_small_airports(gfx.fb, cam, game.db.con)
        #put_gps_text(fb, cam, airport_a, "EFHK")

        gfx.win.addstr( gfx.fb.h//2, gfx.fb.w//2, "X" )

        gfx.win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}")
        #gfx.win.addstr(1,0,f"Controls: wasd to move, zx to zoom, p to toggle reprojection, Enter to animate travel")
        gfx.win.addstr(2,0,f"Closest: {closest_icao}")
        #win.addstr(2,0,f"Distance: { geodesic( (airport_a[1],airport_a[0]), (cam.gps[1],cam.gps[0]) ).km }")
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

        elif ch == ord("p"):
            global disable_mercator
            disable_mercator = not disable_mercator


def menu_find_customers(game):
    customers = game.db.customers_from_airport(game.airport)
    # Make sure airport has at least 3 customers
    for i in range(0, max(3 - len(customers), 0)):
        customer = Customer(game.db)
        customer.generate(game.airport)
        customer.save()
    # Reload customers in case of changes
    customers = game.db.customers_from_airport(game.airport)

    popup = Popup(game)

    i = 0
    for customer in customers:
        i+=1
        if (customer.accepted):
            continue
        popup.add_text(f"#{i}: {customer.name}")
        distance = game.db.icao_distance(customer.origin, customer.destination)
        popup.add_text(f"{customer.origin} -> {customer.destination}")

        popup.add_text(f"Distance: {int(distance)} km")
        popup.add_text(f"Reward:   $ {customer.reward}")
        popup.add_text(f"")
        popup.add_option(f"Board customer #{i}", i)

    popup.add_option(f"Return")
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





class GameState:
    def __init__(self):

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


    def fly_to(self, icao):
        target = icao.upper()

        if not self.db.icao_exists(target):
            return

        gps_a = self.db.airport_xy_icao(self.airport)
        gps_b = self.db.airport_xy_icao(target)

        wp = compute_geodesic(gps_a, gps_b)
        animate_travel(self.gfx, self.cam, wp)

        self.airport = target



def main():
    game = GameState()

    while True:
        game.cam.gps = game.db.airport_xy_icao(game.airport)

        customers_on_board   = game.db.accepted_customers()
        for customer in customers_on_board:
            if game.airport != customer.destination:
                continue
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
        popup.add_option("View your customers (TODO)")
        popup.add_option("Developer options")
        popup.add_option("Quit game")
        action = popup.run()

        if action == "Developer options":
            action = impopup(game, [], ["Freecam", "Reset", "Fly to KJFK", "Return"])
            if action == "Reset":
                game.db.reset()
                impopup(game, ["Database reset"], ["Ok"])
            elif action == "Freecam":
                freecam(game)
            elif action == "Fly to KJFK":
                game.fly_to("KJFK")

        elif action == "Look for customers":
            menu_find_customers(game)


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

