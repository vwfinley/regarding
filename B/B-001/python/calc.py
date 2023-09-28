import math
from collections import namedtuple
Nv = namedtuple('Nv', 'name value')
Nvu = namedtuple('Nvu', 'name value unit')
Point = namedtuple('Point', 'name x y unit')

###
# Inputs
###
CODE = Nv("CODE", 145)
N_PRIME = Nvu("N_PRIME", 0.145, "inches")
T = Nvu("T", 0.039, "inches")
W = Nvu("W", 0.106, "inches")
D_PRIME = Nvu("D_PRIME", 0.036, "inches")
P = Nvu("P", 0.013, "inches")
R1 = Nvu("R1", 0.021, "inches")
R2 = Nvu("R2", 0.023, "inches")
R3 = Nvu("R3", R2.value, R2.unit)

alpha = Nvu("alpha", 3.0, "degrees")

###
# Relative to p1
###
theta = Nvu("theta", math.radians(90.0 - alpha.value), "radians")

p1 = Point("p1", 0.0, 0.0, "inches")
t = Point("t", R1.value * math.cos(theta.value), R1.value * math.sin(theta.value), "inches")

y_g = t.y - P.value
theta_g = Nvu("theta_g", math.asin(y_g / R1.value), "radians")
x_g = R1.value * math.cos(theta_g.value)
g = Point("g", x_g, y_g, "inches")

###
# Relative to g (origin)
###
p1 = Point("p1", p1.x - g.x, p1.y - g.y, "inches")
t = Point("t", t.x - g.x, t.y - g.y, "inches")
g = Point("g", g.x - g.x, g.y - g.y, "inches")

###
# Calc other centers relative to g (origin)
###
p2 = Point("p2", R2.value * math.cos(theta_g.value), R2.value * math.sin(theta_g.value), "inches")
p3 = Point("p3", p2.x - 0.5 * T.value, p2.y, "inches")

###
# Convert/Format for output
###
theta_g = Nvu(theta_g.name, math.degrees(theta_g.value), "degrees")

###
# Outputs
###
print("--- INPUTS ---")
print(alpha)
print(CODE)
print(N_PRIME)
print(T)
print(W)
print(D_PRIME)
print(P)
print(R1)
print(R2)
print(R3)

print("--- OUTPUTS ---")
print(theta_g)
print(t)
print(g)
print(p1)
print(p2)
print(p3)