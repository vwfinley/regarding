import sys, math, json
from argparse import ArgumentParser

from abc import ABC, abstractmethod 


sys.path.insert(0, '../rp25')
from rp25 import *

from collections import namedtuple
Point = namedtuple('Point', 'label x y')

default_code = 110
default_slope = 3.0

on = "black"
off = "lightgray"

def begin_picture(x: float, y: float):
	return "\\begin{{tikzpicture}}[x={}in, y={}in]\n".format(x, y)
def end_picture():
	return "\end{tikzpicture}\n"

def begin_scale(xscale:float, yscale: float):
	return "\\begin{{scope}}[xscale={}, yscale={}]\n".format(xscale, yscale)

def end_scope():
	return "\end{scope}\n"


def xaxis(color: str, x1: float, x2: float):
	return "\\draw[{}, -{{Latex[scale=1.5]}}] ({:.5f}, 0) -- ({:.5f}, 0)  node [right] {{$x$}};\n".format(color, x1, x2)		

def yaxis(color: str, y1: float, y2: float):
	return "\\draw[{}, -{{Latex[scale=1.5]}}] (0, {:.5f}) -- (0, {:.5f})  node [above] {{$y$}};\n".format(color, y1, y2)

def line(color: str, label: str, x1: float, y1: float, x2: float, y2: float):
	return "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x1, y1, x2, y2, label)		

def cline(color: str, label: str, x: float, y: float, angle: float, r1: float, r2: float):
	cos = math.cos(math.radians(angle))
	sin = math.sin(math.radians(angle))
	dx1 = r1 * cos
	dy1 = r1 * sin
	dx2 = r2 * cos
	dy2 = r2 * sin
	return line(color, label, x - dx1, y - dy1, x + dx2, y + dy2)
	

def centermark(color: str, label: str, x: float, y: float):
	len = 0.001
	x1 = x - len
	x2 = x + len
	y1 = y - len
	y2 = y + len
	horiz = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x1, y, x2, y, label)
	vert = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f});\n".format(color, x, y1, x, y2)
	return horiz + vert

def arc(color: str, label: str, x: float, y: float, radius: float, start_angle: float, end_angle: float):
	return "\\draw[{0}] ([shift=({4:.5f} : {3:.5f})] {1:.5f},{2:.5f}) arc ({4:.5f} : {5:.5f} : {3:.5f});\n".format(color, x, y, radius, start_angle, end_angle)

def arrow(color: str, label: str, x: float, y: float, length: float, angle: float):
	dx = length * math.cos(math.radians(angle))
	dy = length * math.sin(math.radians(angle))
	return "\\draw[{}, -{{Latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x, y, x + dx, y + dy, label)		

#--------------
class Drawable(ABC):
	def draw(self) -> str: 
		return self.output

class Begin(Drawable):
	def __init__(self, clip: float, scale: float):
		self.output = "\\begin{{tikzpicture}}[x={0}in, y={0}in]\n".format(clip) + "\\begin{{scope}}[xscale={0}, yscale={0}]\n".format(scale)

class End(Drawable):
	def __init__(self):
		self.output =  "\end{scope}\n" + "\end{tikzpicture}\n"

class XAxis(Drawable):
	def __init__(self, color: str, x1: float, x2: float):
		self.output = "\\draw[{}, -{{Latex[scale=1.5]}}] ({:.5f}, 0) -- ({:.5f}, 0)  node [right] {{$x$}};\n".format(color, x1, x2)		

class YAxis(Drawable):
	def __init__(self, color: str, y1: float, y2: float):
		self.output = "\\draw[{}, -{{Latex[scale=1.5]}}] (0, {:.5f}) -- (0, {:.5f})  node [above] {{$y$}};\n".format(color, y1, y2)


class Line(Drawable):
	def __init__(self, color: str, label: str, x1: float, y1: float, x2: float, y2: float):
		self.output = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x1, y1, x2, y2, label)	

class CLine(Line):
	def __init__(self, color: str, label: str, x: float, y: float, angle: float, r1: float, r2: float):
		cos = math.cos(math.radians(angle))
		sin = math.sin(math.radians(angle))
		dx1 = r1 * cos
		dy1 = r1 * sin
		dx2 = r2 * cos
		dy2 = r2 * sin
		super().__init__(color, label, x - dx1, y - dy1, x + dx2, y + dy2)

class Centermark(Drawable):
	def __init__(self, color: str, label: str, x: float, y: float):
		len = 0.001
		x1 = x - len
		x2 = x + len
		y1 = y - len
		y2 = y + len
		horiz = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x1, y, x2, y, label)
		vert = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f});\n".format(color, x, y1, x, y2)
		self.output = horiz + vert

class Arc(Drawable): 
	def __init__(self, color: str, label: str, x: float, y: float, radius: float, start_angle: float, end_angle: float):
		self.output = "\\draw[{0}] ([shift=({4:.5f} : {3:.5f})] {1:.5f},{2:.5f}) arc ({4:.5f} : {5:.5f} : {3:.5f});\n".format(color, x, y, radius, start_angle, end_angle)

class Arrow(Drawable): 
	def __init__(self, color: str, label: str, x: float, y: float, length: float, angle: float):
		dx = length * math.cos(math.radians(angle))
		dy = length * math.sin(math.radians(angle))
		self.output = "\\draw[{}, -{{Latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n".format(color, x, y, x + dx, y + dy, label)		

def draw(code: int, slope: float):

	results = rp25(code, slope)
	input = results[inputs]
	output = results[outputs]

	print("--- INPUTS ---")
	print(json.dumps(input, indent=2))
	print("--- OUTPUTS ---")
	print(json.dumps(output, indent=2))

	R1 = input["R1"]["value"]
	R2 = input["R2"]["value"]
	R3 = input["R3"]["value"]
	N_PRIME = input["N_PRIME"]["value"]
	T = input["T"]["value"]
	W = input["W"]["value"]
	D_PRIME = input["D_PRIME"]["value"]
	P = input["P"]["value"]

	origin = Point("g", output["g"]["x"], output["g"]["y"])
	p1 = Point("p1", output["p1"]["x"], output["p1"]["y"])
	p2 = Point("p2", output["p2"]["x"], output["p2"]["y"])
	p3 = Point("p3", output["p3"]["x"], output["p3"]["y"])
	theta_g =  output["theta_g"]["value"]

	overhang = 0.005
	with open('output.tikz', 'w') as f:

		f.write(Begin(1, 45).draw())
		
		f.write(XAxis(off, -W - 2 * overhang, T + 2 * overhang).draw())
		f.write(YAxis(off, P - D_PRIME - 2 * overhang , P + 2 * overhang).draw())


		# horiz
		left = -W - overhang
		right = T + overhang
		f.write(Line(off, "", left, P, right, P).draw())
		f.write(Line(off, "", left, P - D_PRIME, right, P - D_PRIME).draw())


		# vert
		top = P + overhang
		bottom = P - D_PRIME - overhang
		f.write(Line(off, "", T, bottom, T, top).draw())
		f.write(Line(off, "", T / 2, bottom, T / 2, top).draw())		
		f.write(Line(off, "", -W, bottom, -W, top).draw())	

		f.write(Centermark(off, p1.label, p1.x, p1.y).draw())	
		f.write(Centermark(off, p2.label, p2.x, p2.y).draw())	
		f.write(Centermark(off, p3.label, p3.x, p3.y).draw())	


		f.write(Arc(off, "c1", p1.x, p1.y, R1, -30, 115).draw())
		f.write(Arc(off, "c2", p2.x, p2.y, R2, 180, 285).draw())
		f.write(Arc(off, "c3", p3.x, p3.y, R3, 255, 360).draw())

		f.write(Arrow(off, "R1", p1.x, p1.y, R1, 75.0).draw())
		f.write(Arrow(off, "R2", p2.x, p2.y, R2, -135.0).draw())
		f.write(Arrow(off, "R3", p3.x, p3.y, R3, -45.0).draw())

		f.write(CLine(off, "L", 0, 0, theta_g, 0.035, 0.035).draw())

		###
		f.write(Arrow(off, "R1", origin.x, origin.y, R1, 180.0 + theta_g - 10.0).draw())
		f.write(Arrow(off, "R2", origin.x, origin.y, R2, theta_g + 10.0).draw())

		f.write(Arc(off, "V1", origin.x, origin.y, R1, 180.0 + theta_g - 15.0, 180.0 + theta_g + 15.0).draw())
		f.write(Arc(off, "V2", origin.x, origin.y, R2, theta_g - 15.0, theta_g + 15.0).draw())

		f.write(End().draw())


#		f.write(begin_picture(1, 1))
#		f.write(begin_scale(45, 45))

#		f.write(xaxis(off, -W - 2 * overhang, T + 2 * overhang))
#		f.write(yaxis(off, P - D_PRIME - 2 * overhang , P + 2 * overhang))

		# horiz
#		left = -W - overhang
#		right = T + overhang
#		f.write(line(off, "", left, P, right, P))
#		f.write(line(off, "", left, P - D_PRIME, right, P - D_PRIME))
		
		# vert
#		top = P + overhang
#		bottom = P - D_PRIME - overhang
#		f.write(line(off, "", T, bottom, T, top))
#		f.write(line(off, "", T / 2, bottom, T / 2, top))		
#		f.write(line(off, "", -W, bottom, -W, top))		

#		f.write(centermark(off, p1.label, p1.x, p1.y))
#		f.write(centermark(off, p2.label, p2.x, p2.y))
#		f.write(centermark(off, p3.label, p3.x, p3.y))

#		f.write(arc(off, "c1", p1.x, p1.y, R1, -30, 115))
#		f.write(arc(off, "c2", p2.x, p2.y, R2, 180, 285))
#		f.write(arc(off, "c3", p3.x, p3.y, R3, 255, 360))

#		f.write(arrow(off, "R1", p1.x, p1.y, R1, 75.0))
#		f.write(arrow(off, "R2", p2.x, p2.y, R2, -135.0))
#		f.write(arrow(off, "R3", p3.x, p3.y, R3, -45.0))

#		f.write(cline(off, "L", 0, 0, theta_g, 0.035, 0.035))

		###
#		f.write(arrow(off, "R1", origin.x, origin.y, R1, 180.0 + theta_g - 10.0))
#		f.write(arrow(off, "R2", origin.x, origin.y, R2, theta_g + 10.0))

#		f.write(arc(off, "V1", origin.x, origin.y, R1, 180.0 + theta_g - 15.0, 180.0 + theta_g + 15.0))
#		f.write(arc(off, "V2", origin.x, origin.y, R2, theta_g - 15.0, theta_g + 15.0))

#		f.write(end_scope())
#		f.write(end_picture())


def main():
	###
	# Handle args
	###
	parser = ArgumentParser(
		prog="figure",
		description="Generate figures for B-001.",
		epilog="Vincent W. Finley, Bear, DE, USA, 2023"
	)

	parser.add_argument(
		"-c",
		"--code",
		default=default_code,
		choices=list(map(lambda k: str(k), data.keys())),
		help="[default={}]".format(str(default_code)) + " Select wheel code.  For example -c 145"
	)

	parser.add_argument(
		"-s",
		"--slope",
		default=default_slope,
		help="[default={}]".format(str(default_slope)) + " Select tread slope angle, 0.0 <= degrees <= 3.0.  For example -s 2.5"
	)
	
	args = parser.parse_args()
	draw(int(args.code), float(args.slope))


# The main entry point for commandline application.
if __name__ == "__main__":
	main()