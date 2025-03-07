#!/usr/bin/env python3
import mariadb
import shapefile
import array
import math
import time
import curses
from geopy.distance import great_circle
from geopy.distance import geodesic

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






def draw_all_airports(fb, cam, con):
    cur = con.cursor()
    query = 'SELECT longitude_deg, latitude_deg, ident FROM airport WHERE type="large_airport"'
    cur.execute(query)

    for (lon, lat, ident) in cur:
        put_gps_text(fb, cam, (lon,lat), f"● {ident}")


def get_airport(con, key):
    cur = con.cursor()
    query = "SELECT longitude_deg, latitude_deg FROM airport WHERE ident=%s"
    cur.execute(query, (key,))
    coords = cur.fetchone()
    if coords == None:
        print("Virheellinen ICAO-koodi")
        exit()
    return [coords[0],coords[1]]





# "In geometry, a geodesic is a curve representing in some sense the locally
# shortest path (arc) between two points in a surface" - Wikipedia
# This is ultimately just a bad sphere lerp

def compute_geodesic(gps_a, gps_b):
    waypoints = []

    a = gps_to_usphere(gps_a)
    b = gps_to_usphere(gps_b)

    steps = 15 # Steps in geodesic

    for t in range(0, steps+1):
        step = (t/steps);

        # Interpolate between two vectors
        c = [
            a[0] + step * (b[0] - a[0]),
            a[1] + step * (b[1] - a[1]),
            a[2] + step * (b[2] - a[2]),
        ]

        vec3_normalize(c)
        gps = usphere_to_gps(c)

        waypoints.append(gps)
    return waypoints




def draw_waypoints(fb, cam, waypoints):
    last = cam.project_gps(waypoints[0])
    for i in range(1, len(waypoints)):
        cur = cam.project_gps(waypoints[i])
        fb.line(last, cur, 1)
        last = cur

def put_gps_text(fb, cam, gps, text):
    label = cam.project_gps(gps)
    x = int(label[0] * fb.w)
    y = int(label[1] * fb.h)
    if not (x < 0 or y < 0 or x >= fb.w or y >= fb.h):
        fb.win.addstr( y, x, text )



# This is the buffer from which ascii graphics are ultimately generated
# Each pixel gets a 32bit value; last 4 bits are "subpixels", other bits
# determine color and such
class Framebuffer:
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
        self.buffer[ int(pixel[1])*self.w + int(pixel[0]) ] |= val | (data<<8)

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
                        if (char & 1<<8):
                            self.win.addch(y, x, lut[block], curses.color_pair(2))
                        else:
                            self.win.addch(y, x, lut[block], curses.color_pair(0))
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

        # Load map data
        self.sf_low  = shapefile.Reader("./data/ne_110m_admin_0_countries/ne_110m_admin_0_countries")
        self.sf_mid  = shapefile.Reader("./data/ne_50m_admin_0_countries/ne_50m_admin_0_countries")
        #sf_high = shapefile.Reader("./data/ne_10m_admin_0_countries/ne_10m_admin_0_countries")

    def draw(self, cam):
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


def animate_travel_linear_disavled(gfx, cam, a, b, final):
    anim_t0 = time.time()
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

        wp = compute_geodesic(cam.gps, final)

        gfx.draw(cam)
        draw_waypoints(gfx.fb, cam, wp)
        gfx.fb.scanout()
        gfx.fb.win.refresh()

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

            gfx.draw(cam)
            draw_waypoints(gfx.fb, cam, wp)
            gfx.fb.scanout()
            gfx.fb.win.refresh()
        anim_t0 = anim_t1


def main():
    con = mariadb.connect(
        host='127.0.0.1',
        port=3306,
        database='flight_game',
        user='metropolia',
        password='metropolia',
        autocommit=True
    )

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
    curses.init_pair(2, 9, 0)
    curses.init_pair(1, 15, 0)


    pos = get_airport(con, "EFHK")
    #airport_b = get_airport(con, "PASC")
    #airport_b = get_airport(con, "KJFK")

    fb = Framebuffer(win)
    cam = Camera()

    gfx = MapRenderer(fb)



    while True:
        t_start = time.time()

        gfx.draw(cam)

        waypoints = compute_geodesic(pos, cam.gps)
        draw_waypoints(fb, cam, waypoints)

        fb.scanout()


        t_end = time.time()

        if (cam.zoom <= 15.0):
            draw_all_airports(fb, cam, con)
        #put_gps_text(fb, cam, airport_a, "EFHK")

        win.addstr(0,0,f"Rendered in {(t_end-t_start)*1000 : 0.2f} ms, zoom {cam.zoom}, lon {cam.gps[0]:.2f} lat {cam.gps[1]:.2f}, {win.getmaxyx()} {gps_to_mercator(cam.gps)}")
        win.addstr(1,0,f"Controls: wasd to move, zx to zoom, p to toggle reprojection")
        win.addstr(2,0,f"{pos}")
        #win.addstr(2,0,f"Distance: { geodesic( (airport_a[1],airport_a[0]), (cam.gps[1],cam.gps[0]) ).km }")
        win.refresh()

        # Input handling
        # Python is stupid
        pan_speed = 0.1
        ch = win.getch()
        if ch == ord("q"):
            break

        elif ch == ord("a"):
            cam.gps[0] -= cam.zoom * pan_speed

        elif ch == ord("d"):
            cam.gps[0] += cam.zoom * pan_speed

        elif ch == ord("w"):
            cam.gps[1] += cam.zoom * pan_speed

        elif ch == ord("s"):
            cam.gps[1] -= cam.zoom * pan_speed

        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:

            for gps in waypoints:
                cam.gps[0] = gps[0]
                cam.gps[1] = gps[1]
                gfx.draw(cam)
                fb.scanout()
                win.refresh()

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


    win.keypad(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()


if __name__ == "__main__":
    main()

