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
from vec3 import *

# Map.py

# This file contains rendering logic and map projection related functions, all
# the complex map stuff.

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

#disable_mercator = False
def gps_to_mercator(gps):
    #if (disable_mercator):
    #    return gps
    w = 360
    h = 180
    x = gps[0]

    lat = math.radians( max(min(gps[1], 87), -87)  )

    mercN = math.log( math.tan( (math.pi/4) + (lat/2)) )
    y = (w * mercN/(2*math.pi))

    return [x,y]




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


    def draw_waypoints(self, cam, waypoints):
        last = cam.project_gps(waypoints[0])
        for i in range(1, len(waypoints)):
            cur = cam.project_gps(waypoints[i])
            self.fb.line(last, cur, 1)
            last = cur





