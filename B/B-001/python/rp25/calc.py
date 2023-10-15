import math
import keys
from common import *

from collections import namedtuple
Point = namedtuple('Point', 'x y')

def calculate(slope, T, P, R1, R2, R3) -> dict:

	###
	# Relative to p1
	###
	theta_s = math.radians(slope) # radians
	p1 = Point(0.0, 0.0)
	ps = Point(R1 * math.sin(theta_s), R1 * math.cos(theta_s))

	y_pg = ps.y - P
	theta_g = math.asin(y_pg / R1) # radians
	x_pg = R1 * math.cos(theta_g)
	pg = Point(x_pg, y_pg)

	###
	# Translate to g (origin)
	###
	p1 = Point(p1.x - pg.x, p1.y - pg.y)
	ps = Point(ps.x - pg.x, ps.y - pg.y)
	pg = Point(pg.x - pg.x, pg.y - pg.y)

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
	# Calc pd (for convenience)
	###
	local_x = p2.x - T/2
	local_h = R2
	local_y = math.sqrt(local_h * local_h - local_x * local_x)
	pd = Point(T/2,  p2.y - local_y)

	###
	# Calc d_prime (for convenience)
	###
	d_prime = ps.y - pd.y


	###
	# Gather results
	###
	return {
		keys.pg: {x: pg.x, y: pg.y, unit: inches},
		keys.theta_g: {value: theta_g, unit: degrees},
		keys.ps: {x: ps.x, y: ps.y, unit: inches},
		keys.pd: {x: pd.x, y: pd.y, unit: inches},
		keys.p1: {x: p1.x, y: p1.y, unit: inches},
		keys.p2: {x: p2.x, y: p2.y, unit: inches},
		keys.p3: {x: p3.x, y: p3.y, unit: inches},
		keys.d_prime: {value: d_prime, unit: inches}
	}