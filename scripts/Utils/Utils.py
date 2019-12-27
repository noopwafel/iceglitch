''' Random utility functions '''

from random import randint, uniform
import subprocess


def hex_ascii(data):
    '''converts a byte string into string with non-printable ascii as dots'''
    ret = ''
    for dat in data:
        if 0x20 <= dat <= 0x80:
            ret += chr(dat)
        else:
            ret += '.'
    return ret

def random_float(min_v, max_v, repeat=1):
    ''' Parameter generator which can take a repeat'''
    while True:
        val = uniform(min_v, max_v)
        for i in range(repeat):
            i = i
            yield val

def random_int(min_v, max_v, repeat=1):
    ''' Parameter generator which can take a repeat'''
    while True:
        val = randint(min_v, max_v)
        for i in range(repeat):
            i = i
            return val


def run_command(command):
    ''' Run a command in a shell, no user supplied input allowed
        but why is the sentence so long?
    '''
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()


def random_in_poly(x_coords, y_coords):
    ''' Returns coordinates within a polygon from a uniform distribution'''

    # We compute the bounding box of the polygon and then repeatedly
    # Pick a point in the bounding box until we find one which is within the polygon
    # We're not expecting pathological polygons (uh-oh)
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    poly = Polygon(x_coords, y_coords)
    print("minx", min_x, "max_x", max_x)
    print("miny", min_y, "max_y", max_y)

    while True:
        x, y = 0, 0
        while True:
            x, y = uniform(min_x, max_x), uniform(min_y, max_y)

            if poly.is_inside(x, y) > 0:
                break
        return x, y

            

'''FROM:  https://code.activestate.com/recipes/578381-a-point-in-polygon-program-sw-sloan-algorithm/ '''
'''Class to compute if a point lies inside/outside/on-side of a polygon.

This is a Python 3 implementation of the Sloan's improved version of the
Nordbeck and Rystedt algorithm, published in the paper:

SLOAN, S.W. (1985): A point-in-polygon program.
    Adv. Eng. Software, Vol 7, No. 1, pp 45-47.

This class has 1 method (is_inside) that returns the minimum distance to the
nearest point of the polygon:

If is_inside < 0 then point is outside the polygon.
If is_inside = 0 then point in on a side of the polygon.
If is_inside > 0 then point is inside the polygon.

'''

import numpy as np


def _det(xvert, yvert):
    '''Compute twice the area of the triangle defined by points with using
    determinant formula.

    Input parameters:

    xvert -- A vector of nodal x-coords (array-like).
    yvert -- A vector of nodal y-coords (array-like).

    Output parameters:

    Twice the area of the triangle defined by the points.

    Notes:

    _det is positive if points define polygon in anticlockwise order.
    _det is negative if points define polygon in clockwise order.
    _det is zero if at least two of the points are concident or if
        all points are collinear.

    '''
    xvert = np.asfarray(xvert)
    yvert = np.asfarray(yvert)
    x_prev = np.concatenate(([xvert[-1]], xvert[:-1]))
    y_prev = np.concatenate(([yvert[-1]], yvert[:-1]))
    return np.sum(yvert * x_prev - xvert * y_prev, axis=0)


class Polygon:
    '''Polygon object.

    Input parameters:

    x -- A sequence of nodal x-coords.
    y -- A sequence of nodal y-coords.

    '''

    def __init__(self, x, y):
        if len(x) != len(y):
            raise IndexError('x and y must be equally sized.')
        self.x = np.asfarray(x)
        self.y = np.asfarray(y)
        # Closes the polygon if were open
        x1, y1 = x[0], y[0]
        xn, yn = x[-1], y[-1]
        if x1 != xn or y1 != yn:
            self.x = np.concatenate((self.x, [x1]))
            self.y = np.concatenate((self.y, [y1]))
        # Anti-clockwise coordinates
        if _det(self.x, self.y) < 0:
            self.x = self.x[::-1]
            self.y = self.y[::-1]

    def is_inside(self, xpoint, ypoint, smalld=1e-12):
        '''Check if point is inside a general polygon.

        Input parameters:

        xpoint -- The x-coord of the point to be tested.
        ypoint -- The y-coords of the point to be tested.
        smalld -- A small float number.

        xpoint and ypoint could be scalars or array-like sequences.

        Output parameters:

        mindst -- The distance from the point to the nearest point of the
                  polygon.
                  If mindst < 0 then point is outside the polygon.
                  If mindst = 0 then point in on a side of the polygon.
                  If mindst > 0 then point is inside the polygon.

        Notes:

        An improved version of the algorithm of Nordbeck and Rydstedt.

        REF: SLOAN, S.W. (1985): A point-in-polygon program. Adv. Eng.
             Software, Vol 7, No. 1, pp 45-47.

        '''
        xpoint = np.asfarray(xpoint)
        ypoint = np.asfarray(ypoint)
        # Scalar to array
        if xpoint.shape is tuple():
            xpoint = np.array([xpoint], dtype=float)
            ypoint = np.array([ypoint], dtype=float)
            scalar = True
        else:
            scalar = False
        # Check consistency
        if xpoint.shape != ypoint.shape:
            raise IndexError('x and y has different shapes')
        # If snear = True: Dist to nearest side < nearest vertex
        # If snear = False: Dist to nearest vertex < nearest side
        snear = np.ma.masked_all(xpoint.shape, dtype=bool)
        # Initialize arrays
        mindst = np.ones_like(xpoint, dtype=float) * np.inf
        j = np.ma.masked_all(xpoint.shape, dtype=int)
        x = self.x
        y = self.y
        n = len(x) - 1  # Number of sides/vertices defining the polygon
        # Loop over each side defining polygon
        for i in range(n):
            d = np.ones_like(xpoint, dtype=float) * np.inf
            # Start of side has coords (x1, y1)
            # End of side has coords (x2, y2)
            # Point has coords (xpoint, ypoint)
            x1 = x[i]
            y1 = y[i]
            x21 = x[i + 1] - x1
            y21 = y[i + 1] - y1
            x1p = x1 - xpoint
            y1p = y1 - ypoint
            # Points on infinite line defined by
            #     x = x1 + t * (x1 - x2)
            #     y = y1 + t * (y1 - y2)
            # where
            #     t = 0    at (x1, y1)
            #     t = 1    at (x2, y2)
            # Find where normal passing through (xpoint, ypoint) intersects
            # infinite line
            t = -(x1p * x21 + y1p * y21) / (x21 ** 2 + y21 ** 2)
            tlt0 = t < 0
            tle1 = (0 <= t) & (t <= 1)
            # Normal intersects side
            d[tle1] = ((x1p[tle1] + t[tle1] * x21) ** 2 +
                       (y1p[tle1] + t[tle1] * y21) ** 2)
            # Normal does not intersects side
            # Point is closest to vertex (x1, y1)
            # Compute square of distance to this vertex
            d[tlt0] = x1p[tlt0] ** 2 + y1p[tlt0] ** 2
            # Store distances
            mask = d < mindst
            mindst[mask] = d[mask]
            j[mask] = i
            # Point is closer to (x1, y1) than any other vertex or side
            snear[mask & tlt0] = False
            # Point is closer to this side than to any other side or vertex
            snear[mask & tle1] = True
        if np.ma.count(snear) != snear.size:
            raise IndexError('Error computing distances')
        mindst **= 0.5
        # Point is closer to its nearest vertex than its nearest side, check if
        # nearest vertex is concave.
        # If the nearest vertex is concave then point is inside the polygon,
        # else the point is outside the polygon.
        jo = j.copy()
        jo[j == 0] -= 1
        area = _det([x[j + 1], x[j], x[jo - 1]], [y[j + 1], y[j], y[jo - 1]])
        mindst[~snear] = np.copysign(mindst, area)[~snear]
        # Point is closer to its nearest side than to its nearest vertex, check
        # if point is to left or right of this side.
        # If point is to left of side it is inside polygon, else point is
        # outside polygon.
        area = _det([x[j], x[j + 1], xpoint], [y[j], y[j + 1], ypoint])
        mindst[snear] = np.copysign(mindst, area)[snear]
        # Point is on side of polygon
        mindst[np.fabs(mindst) < smalld] = 0
        # If input values were scalar then the output should be too
        if scalar:
            mindst = float(mindst)
        return mindst
