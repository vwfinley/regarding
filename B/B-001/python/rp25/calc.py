import math
import keys
from common import *

from collections import namedtuple
Point = namedtuple('Point', 'x y')

def calculate(slope, T, P, R1, R2, R3) -> dict:

	###
	# Relative to p1
	###
	theta = math.radians(90.0 - slope) # radians
	p1 = Point(0.0, 0.0)
	t = Point(R1 * math.cos(theta), R1 * math.sin(theta))

	y_g = t.y - P
	theta_g = math.asin(y_g / R1) # radians
	x_g = R1 * math.cos(theta_g)
	g = Point(x_g, y_g)

	###
	# Translate to g (origin)
	###
	p1 = Point(p1.x - g.x, p1.y - g.y)
	t = Point(t.x - g.x, t.y - g.y)
	g = Point(g.x - g.x, g.y - g.y)

	###
	# Calc other centers relative to g (origin)
	###
	p2 = Point(R2 * math.cos(theta_g), R2 * math.sin(theta_g))
	p3 = Point(T - p2.x, p2.y) # Reflect p2 across T/2 line

	###
	# Convert for output
	###
	theta_g = math.degrees(theta_g) # degrees

	###
	# Gather results
	###
	return {
		keys.g: {x: g.x, y: g.y, unit: inches},
		keys.theta_g: {value: theta_g, unit: degrees},
		keys.t: {x: t.x, y: t.y, unit: inches},
		keys.p1: {x: p1.x, y: p1.y, unit: inches},
		keys.p2: {x: p2.x, y: p2.y, unit: inches},
		keys.p3: {x: p3.x, y: p3.y, unit: inches}
	}