import sys, math, json
from argparse import ArgumentParser
from abc import ABC, abstractmethod 
from enum import Enum

sys.path.insert(0, '../rp25')
from rp25 import *

from collections import namedtuple
Point = namedtuple('Point', 'label x y')

default_code = 110
default_slope = 3.0
region = 1
scale = 45
overhang = 0.005

class State(Enum):
	Hide = 0
	Off = 1
	On = 2
	
class Drawable(ABC):
	def draw(self, state: State = State.On) -> str: 
		match state:
			case State.Hide:
				return ""
			case State.Off:
				return self.off
			case State.On:
				return self.on

class Begin(Drawable):
	def __init__(self, clip: float, scale: float):
		self.off = self.on = "\\begin{{tikzpicture}}[x={0}in, y={0}in]\n".format(clip) + "\\begin{{scope}}[xscale={0}, yscale={0}]\n".format(scale)

class End(Drawable):
	def __init__(self):
		self.off = self.on = "\end{scope}\n" + "\end{tikzpicture}\n"

class XAxis(Drawable):
	def __init__(self, offcolor: str, oncolor: str, x1: float, x2: float):
		s = "\\draw[{}, -{{Latex[scale=1.5]}}] ({:.5f}, 0) -- ({:.5f}, 0)  node [right] {{$x$}};\n"
		self.off = s.format(offcolor, x1, x2)		
		self.on = s.format(oncolor, x1, x2)		

class YAxis(Drawable):
	def __init__(self, offcolor: str, oncolor: str, y1: float, y2: float):
		s = "\\draw[{}, -{{Latex[scale=1.5]}}] (0, {:.5f}) -- (0, {:.5f})  node [above] {{$y$}};\n"
		self.off = s.format(offcolor, y1, y2)
		self.on = s.format(oncolor, y1, y2)

class Line(Drawable):
	def __init__(self, offcolor: str, oncolor: str, label: str, x1: float, y1: float, x2: float, y2: float):
		s = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n"
		self.off = s.format(offcolor, x1, y1, x2, y2, label)	
		self.on = s.format(oncolor, x1, y1, x2, y2, label)	

class CLine(Line):
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, angle: float, r1: float, r2: float):
		cos = math.cos(math.radians(angle))
		sin = math.sin(math.radians(angle))
		dx1 = r1 * cos
		dy1 = r1 * sin
		dx2 = r2 * cos
		dy2 = r2 * sin
		super().__init__(offcolor, oncolor, label, x - dx1, y - dy1, x + dx2, y + dy2)

class Centermark(Drawable):
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float):
		len = 0.001
		x1 = x - len
		x2 = x + len
		y1 = y - len
		y2 = y + len
		h = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n"
		v = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f});\n"	
		self.off = h.format(offcolor, x1, y, x2, y, label) + v.format(offcolor, x, y1, x, y2)
		self.on = h.format(oncolor, x1, y, x2, y, label) + v.format(oncolor, x, y1, x, y2)

class Arc(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, radius: float, start_angle: float, end_angle: float):
		s = "\\draw[{0}] ([shift=({4:.5f} : {3:.5f})] {1:.5f},{2:.5f}) arc ({4:.5f} : {5:.5f} : {3:.5f});\n"
		self.off = s.format(offcolor, x, y, radius, start_angle, end_angle)
		self.on = s.format(oncolor, x, y, radius, start_angle, end_angle)

class Arrow(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, length: float, angle: float):
		dx = length * math.cos(math.radians(angle))
		dy = length * math.sin(math.radians(angle))
		s = "\\draw[{}, -{{Latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [right] {{${}$}};\n"
		self.off = s.format(offcolor, x, y, x + dx, y + dy, label)
		self.on = s.format(oncolor, x, y, x + dx, y + dy, label)

figs = {
	"fig1": {
		"begin": State.On,

		"x_axis": State.On,
		"y_axis": State.On,

		"line_P": State.Off,
		"line_Dprime": State.Off,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_W": State.Off,

		"center_p1": State.Off,
		"center_p2": State.Off,
		"center_p3": State.Off,

		"arc_c1": State.Off,
		"arc_c2": State.Off,
		"arc_c3": State.Off,

		"arrow_r1": State.Off,
		"arrow_r2": State.Off,
		"arrow_r3": State.Off,

		"cline_L": State.Off,

		"arrow_r1_layout": State.Off,
		"arrow_r2_layout": State.Off,

		"arc_v1": State.Off,
		"arc_v2": State.Off,

		"end": State.On
	},
	"fig2": {
		"begin": State.On,

		"x_axis": State.On,
		"y_axis": State.On,

		"line_P": State.Off,
		"line_Dprime": State.Off,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_W": State.Off,

		"center_p1": State.Off,
		"center_p2": State.Off,
		"center_p3": State.Off,

		"arc_c1": State.On,
		"arc_c2": State.On,
		"arc_c3": State.On,

		"arrow_r1": State.Off,
		"arrow_r2": State.Off,
		"arrow_r3": State.Off,

		"cline_L": State.Off,

		"arrow_r1_layout": State.Off,
		"arrow_r2_layout": State.Off,

		"arc_v1": State.Off,
		"arc_v2": State.Off,

		"end": State.On
	}
}

def Draw(drawables: dict, d: dict, filename: str):
	with open(filename, 'w') as f:
		for key, value in d.items():
			f.write(drawables[key].draw(value))

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

	# -------------------------
	drawables = {}

	drawables["begin"] = Begin(region, scale)
	drawables["end"] = End()

	drawables["x_axis"] = XAxis("lightgray", "black", -W - 2 * overhang, T + 2 * overhang)
	drawables["y_axis"] = YAxis("lightgray", "black", P - D_PRIME - 2 * overhang , P + 2 * overhang)

	# h lines
	left = -W - overhang
	right = T + overhang
	drawables["line_P"] = Line("lightgray", "black", "", left, P, right, P)
	drawables["line_Dprime"] = Line("lightgray", "black", "", left, P - D_PRIME, right, P - D_PRIME)

	# v lines
	top = P + overhang
	bottom = P - D_PRIME - overhang
	drawables["line_T"] = Line("lightgray", "black", "", T, bottom, T, top)
	drawables["line_T2"] = Line("lightgray", "black", "", T / 2, bottom, T / 2, top)
	drawables["line_W"] = Line("lightgray", "black", "", -W, bottom, -W, top)

	# centermarks
	drawables["center_p1"] = Centermark("lightgray", "black", p1.label, p1.x, p1.y)
	drawables["center_p2"] = Centermark("lightgray", "black", p2.label, p2.x, p2.y)
	drawables["center_p3"] = Centermark("lightgray", "black", p3.label, p3.x, p3.y)

	# arcs
	drawables["arc_c1"] = Arc("lightgray", "black", "c1", p1.x, p1.y, R1, -30, 115)
	drawables["arc_c2"] = Arc("lightgray", "black", "c2", p2.x, p2.y, R2, 180, 285)
	drawables["arc_c3"] = Arc("lightgray", "black", "c3", p3.x, p3.y, R3, 255, 360)

	# arrows
	drawables["arrow_r1"] = Arrow("lightgray", "black", "R1", p1.x, p1.y, R1, 75.0)
	drawables["arrow_r2"] = Arrow("lightgray", "black", "R2", p2.x, p2.y, R2, -135.0)
	drawables["arrow_r3"] = Arrow("lightgray", "black", "R3", p3.x, p3.y, R3, -45.0)

	# clines
	drawables["cline_L"] = CLine("lightgray", "black", "L", 0, 0, theta_g, 0.035, 0.035)

	# arrows
	drawables["arrow_r1_layout"] = Arrow("lightgray", "black", "R1", origin.x, origin.y, R1, 180.0 + theta_g - 10.0)
	drawables["arrow_r2_layout"] = Arrow("lightgray", "black", "R2", origin.x, origin.y, R2, theta_g + 10.0)

	# arcs
	drawables["arc_v1"] = Arc("lightgray", "black", "V1", origin.x, origin.y, R1, 180.0 + theta_g - 15.0, 180.0 + theta_g + 15.0)
	drawables["arc_v2"] = Arc("lightgray", "black", "V2", origin.x, origin.y, R2, theta_g - 15.0, theta_g + 15.0)

	for key, value in figs.items():
		Draw(drawables, value, key + ".tikz")


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