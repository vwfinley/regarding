import os, sys, math, json, shutil
from argparse import ArgumentParser
from abc import ABC, abstractmethod 
from enum import Enum

sys.path.insert(0, '../rp25')
from rp25 import *

from collections import namedtuple
Point = namedtuple('Point', 'label x y')

default_code = 110
default_outdir = "output"
default_slope = 3.0
region = 1
scale = 45
overhang = 0.007

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


class Clip(Drawable):
	def __init__(self, left: float, top: float, w: float, h: float):
		s = "\\clip ({:.5f}, {:.5f}) rectangle ({:.5f}, {:.5f});\n"
		self.on = self.off = s.format(left, top, w, h)

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

class Pointmark(Drawable):
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, x_label_offset: float, y_label_offset: float):
		s = "\\filldraw[{}] ({:.5f}, {:.5f}) circle (0.02pt) node [shift={{({:.5f}, {:.5f})}}]  {{${}$}};\n"
		self.off = s.format(offcolor, x , y, x_label_offset, y_label_offset, label)
		self.on = s.format(oncolor, x , y, x_label_offset, y_label_offset, label)

class Arc(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, radius: float, start_angle: float, end_angle: float):
		s = "\\draw[{0}] ([shift=({4:.5f} : {3:.5f})] {1:.5f},{2:.5f}) arc ({4:.5f} : {5:.5f} : {3:.5f});\n"
		self.off = s.format(offcolor, x, y, radius, start_angle, end_angle)
		self.on = s.format(oncolor, x, y, radius, start_angle, end_angle)


class ArcArrow(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, atstart: bool, x: float, y: float, radius: float, start_angle: float, end_angle: float):
		if atstart:
			s = "\\draw[{0}, -{{Latex[scale=0.75]}}] ([shift=({5:.5f} : {4:.5f})] {2:.5f},{3:.5f}) arc ({5:.5f} : {6:.5f} : {4:.5f}) node [right] {{${1}$}};\n"
		else:
			s = "\\draw[{0}, {{Latex[scale=0.75]}}-] ([shift=({5:.5f} : {4:.5f})] {2:.5f},{3:.5f}) arc ({5:.5f} : {6:.5f} : {4:.5f}) node [right] {{${1}$}};\n"
		self.off = s.format(offcolor, label, x, y, radius, start_angle, end_angle)
		self.on = s.format(oncolor, label, x, y, radius, start_angle, end_angle)

class Arrow(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, atstart: bool, x: float, y: float, length: float, angle: float, x_label_offset: float, y_label_offset: float):
		dx = length * math.cos(math.radians(angle))
		dy = length * math.sin(math.radians(angle))
		if atstart:
			s = "\\draw[{}, {{Latex[scale=0.75]}}-{{Latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f}) node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"
		else:
			s = "\\draw[{}, -{{Latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"

		self.off = s.format(offcolor, x, y, x + dx, y + dy, x_label_offset, y_label_offset, label)
		self.on = s.format(oncolor, x, y, x + dx, y + dy, x_label_offset, y_label_offset, label)


figs = {
	"fig1": {
		"begin": State.On,
		"clip": State.On,

#		"x_axis": State.Off,
#		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.On,
		"line_ps_p1": State.On,
		"line_slope_corner_1": State.On,
		"line_slope_corner_2": State.On,

#		"centermark_p1": State.Off,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

#		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,

#		"arc_slope": State.On,
		"arc_slope_upper": State.On,
		"arc_slope_lower": State.On,

#		"arc_c1": State.Off,
#		"arc_c2": State.Off,
#		"arc_c3": State.Off,
#		"arc_ps_p1": State.On,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.On,
#
#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,


		"end": State.On
	},
	"fig2": {
		"begin": State.On,
		"clip": State.On,

#		"x_axis": State.Off,
#		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

#		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

#		"arc_c1": State.Off,
#		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.On,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
		"arrow_ps_p1": State.On,

#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,
		"end": State.On
	},
	"fig3": {
		"begin": State.On,
		"clip": State.On,

#		"x_axis": State.Off,
#		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
		"line_false_x_axis": State.On,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"arc_c1": State.On,
#		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

		"arrow_r1": State.On,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,

#		"cline_L": State.On,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,
		"end": State.On
	},
	"fig4": {
		"begin": State.On,
		"clip": State.On,

		"x_axis": State.On,
		"y_axis": State.On,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"arc_c1": State.Off,
#		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,

#		"cline_L": State.On,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,
		"end": State.On
	},
	"fig5": {
		"begin": State.Off,
		"clip": State.Off,

		"x_axis": State.Off,
		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"arc_c1": State.Off,
#		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,

		"cline_L": State.On,

#		"arrow_r1_layout": State.Off,
		"arrow_r2_layout": State.On,

#		"arc_v1": State.Off,
		"arc_v2": State.On,
		"end": State.On
	},
	"fig6": {
		"begin": State.Off,
		"clip": State.Off,

		"x_axis": State.Off,
		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"arc_c1": State.Off,
		"arc_c2": State.On,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
#		"arrow_T": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
		"arrow_r2": State.On,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,

		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
		"arc_v2": State.Off,
		"end": State.On
	},
	"fig7": {
		"begin": State.Off,
		"clip": State.Off,

		"x_axis": State.Off,
		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,

		"line_T": State.On,
		"line_T2": State.On,
		"line_Tbase_dim": State.On,
		"line_T_dim": State.On,
		"line_T2_dim": State.On,


#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"arc_c1": State.Off,
		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
		"arrow_T": State.On,
		"arrow_T2": State.On,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,

		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
		"arc_v2": State.Off,
		"end": State.On
	},
	"fig8": {
		"begin": State.Off,
		"clip": State.Off,

		"x_axis": State.Off,
		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,
		"line_p2_p3":  State.On,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_Tbase_dim": State.Off,
		"line_T_dim": State.Off,
		"line_T2_dim": State.Off,

#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"arc_c1": State.Off,
		"arc_c2": State.Off,
#		"arc_c3": State.Off,
		"arc_ps_p1": State.Off,
		"arc_p3": State.On,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
		"arrow_T": State.Off,
		"arrow_T2": State.Off,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,
		"arrow_p3": State.On,

		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
		"arc_v2": State.Off,
		"end": State.On
	},
	"fig9": {
		"begin": State.Off,
		"clip": State.Off,

		"x_axis": State.Off,
		"y_axis": State.Off,

		"line_P": State.Off,
#		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,
		"line_p2_p3":  State.Off,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_Tbase_dim": State.Off,
		"line_T_dim": State.Off,
		"line_T2_dim": State.Off,


#		"line_W": State.Off,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"arc_c1": State.Off,
		"arc_c2": State.Off,
		"arc_c3": State.On,
		"arc_ps_p1": State.Off,
		"arc_p3": State.Off,

#		"arrow_NPrime": State.On,
#		"arrow_W": State.On,
		"arrow_T": State.Off,
		"arrow_T2": State.Off,
#		"arrow_P": State.On,
#		"arrow_DPrime": State.On,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
		"arrow_r3": State.On,
#		"arrow_ps_p1": State.Off,
#		"arrow_p3": State.Off,

		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
		"arc_v2": State.Off,
		"end": State.On
	},
	"fig99": {
		"begin": State.On,
		"clip": State.On,

		"x_axis": State.On,
		"y_axis": State.On,

		"line_P": State.Off,
		"line_Dprime": State.Off,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_W": State.Off,

		"line_slope": State.On,
		"line_ps_p1": State.On,
		"line_slope_corner_1": State.On,
		"line_slope_corner_2": State.On,

		"centermark_p1": State.Off,
		"centermark_p2": State.Off,
		"centermark_p3": State.Off,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,


		"arc_c1": State.On,
		"arc_c2": State.On,
		"arc_c3": State.On,
		"arc_ps_p1": State.On,

		"arrow_NPrime": State.Off,
		"arrow_W": State.Off,
		"arrow_T": State.Off,
		"arrow_T2": State.Off,
		"arrow_P": State.Off,
		"arrow_DPrime": State.Off,

		"arrow_r1": State.Off,
		"arrow_r2": State.Off,
		"arrow_r3": State.Off,
		"arrow_ps_p1": State.On,

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

def draw(code: int, slope: float, outdir: str):
	results = rp25(code, slope)
	input = results[inputs]
	output = results[outputs]

	oncolor = "black"
	offcolor = "lightgray"

	print("--- INPUTS ---")
	print(json.dumps(input, indent=2))
	print("--- OUTPUTS ---")
	print(json.dumps(output, indent=2))

	N_PRIME = input["N_PRIME"]["value"]
	T = input["T"]["value"]
	W = input["W"]["value"]
	D_PRIME = input["D_PRIME"]["value"]
	P = input["P"]["value"]
	R1 = input["R1"]["value"]
	R2 = input["R2"]["value"]
	R3 = input["R3"]["value"]
	slope = input["slope"]["value"]

	pg = Point("p_g", output["pg"]["x"], output["pg"]["y"])
	theta_g =  output["theta_g"]["value"]
	ps = Point("p_s", output["ps"]["x"], output["ps"]["y"])
	pd = Point("p_d", output["pd"]["x"], output["pd"]["y"])
	p1 = Point("p_1", output["p1"]["x"], output["p1"]["y"])
	p2 = Point("p_2", output["p2"]["x"], output["p2"]["y"])
	p3 = Point("p_3", output["p3"]["x"], output["p3"]["y"])
	d_prime =  output["d_prime"]["value"]

	# -------------------------
	drawables = {}

	drawables["begin"] = Begin(region, scale)
	drawables["end"] = End()
	drawables["clip"] = Clip(-.021, -.030, .05,.05)

	drawables["x_axis"] = XAxis(offcolor, oncolor, -W - 2 * overhang, T + 2 * overhang)
	drawables["y_axis"] = YAxis(offcolor, oncolor, P - D_PRIME - 2 * overhang , P + 2 * overhang)

	# h lines
	left = -W - overhang
	right = T + overhang
	drawables["line_P"] = Line(offcolor, oncolor, "", left, P, right, P)
	drawables["line_false_x_axis"] = Line(offcolor, oncolor, "", -1, 0, 1, 0)
	drawables["line_Dprime"] = Line(offcolor, oncolor, "", left, P - D_PRIME, right, P - D_PRIME)

	drawables["line_p2_p3"] = Line(offcolor, oncolor, "", p2.x - 0.006, p2.y, p3.x + 0.006, p3.y)

	# v lines
	top = P + overhang
	bottom = P - D_PRIME - overhang
	drawables["line_T"] = Line(offcolor, oncolor, "", T, bottom, T, top)
	drawables["line_T2"] = Line(offcolor, oncolor, "", T / 2, bottom, T / 2, top)
# VWF
	drawables["line_Tbase_dim"] = Line(offcolor, oncolor, "", 0, 2.9 * P, 0, 3.6 * P)
	drawables["line_T_dim"] = Line(offcolor, oncolor, "", T, 3.4 * P, T, 3.6 * P)
	drawables["line_T2_dim"] = Line(offcolor, oncolor, "", T / 2, 2.9 * P, T / 2, 3.1 * P)

	drawables["line_W"] = Line(offcolor, oncolor, "", -W, bottom, -W, top)

	# diag lines
	slope1 =  math.radians(0.0 - slope)
	slope2 = math.radians(180.0 - slope)
	l1 = 0.8 * T
	l2 = 0.9 * W
	x1 = l1 * math.cos(slope1)
	y1 = l1 * math.sin(slope1)
	x2 = l2 * math.cos(slope2)
	y2 = l2 * math.sin(slope2)
	drawables["line_slope"] = Line(offcolor, oncolor, "slope", ps.x + x1, ps.y + y1, ps.x + x2, ps.y + y2)  # Tread slope

	len = 0.001
	slope1 =  math.radians(180.0 - slope)
	slope2 = math.radians(135.0 - slope)
	x1 = len * 1.0 * math.cos(slope1)
	y1 = len * 1.0 * math.sin(slope1)
	x2 = len * 1.414 * math.cos(slope2)
	y2 = len * 1.414 * math.sin(slope2)
	drawables["line_slope_corner_1"] = Line(offcolor, oncolor, "", ps.x - x1, ps.y - y1, ps.x - x2, ps.y - y2)  # 

	slope3 = math.radians(90.0 - slope)
	x3 = len * 1.0 * math.cos(slope3)
	y3 = len * 1.0 * math.sin(slope3)
	drawables["line_slope_corner_2"] = Line(offcolor, oncolor, "", ps.x - x2, ps.y - y2, ps.x - x3, ps.y - y3)  # 

	slope1 =  math.radians(90.0 - slope)
	slope2 = math.radians(270.0 - slope)
	x1 = 0.5 * R1 * math.cos(slope1)
	y1 = 0.5 * R1 * math.sin(slope1)
	x2 = 1.5 * R1 * math.cos(slope2)
	y2 = 1.5 * R1 * math.sin(slope2)
	drawables["line_ps_p1"] = Line(offcolor, oncolor, "", ps.x + x1, ps.y + y1, ps.x + x2, ps.y + y2)  # ps->p1 line

	# centermarks
	drawables["centermark_p1"] = Centermark(offcolor, oncolor, p1.label, p1.x, p1.y)
	drawables["centermark_p2"] = Centermark(offcolor, oncolor, p2.label, p2.x, p2.y)
	drawables["centermark_p3"] = Centermark(offcolor, oncolor, p3.label, p3.x, p3.y)

	# pointmarks
	drawables["pointmark_pg"] = Pointmark(offcolor, oncolor, pg.label, pg.x, pg.y, 0.14, -0.07)
	drawables["pointmark_ps"] = Pointmark(offcolor, oncolor, ps.label, ps.x, ps.y, 0.13, -0.08)
	drawables["pointmark_pd"] = Pointmark(offcolor, oncolor, pd.label, pd.x, pd.y, 0.13, -0.07)
	drawables["pointmark_p1"] = Pointmark(offcolor, oncolor, p1.label, p1.x, p1.y, 0.13, -0.07)
	drawables["pointmark_p2"] = Pointmark(offcolor, oncolor, p2.label, p2.x, p2.y, 0.13, -0.07)
	drawables["pointmark_p3"] = Pointmark(offcolor, oncolor, p3.label, p3.x, p3.y, -0.14, 0)

	# arcs
	drawables["arc_c1"] = Arc(offcolor, oncolor, "c1", p1.x, p1.y, R1, -30, 115)
	drawables["arc_c2"] = Arc(offcolor, oncolor, "c2", p2.x, p2.y, R2, 180, 285)
	drawables["arc_c3"] = Arc(offcolor, oncolor, "c3", p3.x, p3.y, R3, 255, 360)
	drawables["arc_p3"] = Arc(offcolor, oncolor, "p3",  T / 2, p3.y,  T / 2 - p3.x, 140, 240)

	arc_slope_radius = 0.023
	drawables["arc_slope_upper"] = ArcArrow(offcolor, oncolor, "", False, ps.x, ps.y,  arc_slope_radius , 0, 10)
	drawables["arc_slope_lower"] = ArcArrow(offcolor, oncolor, "slope", True, ps.x, ps.y, arc_slope_radius , 360 - slope - 10, 360 - slope)

	# arrows (layout)
	drawables["arrow_NPrime"] = Arrow(offcolor, oncolor, "N'", True, -W, 3.5 * P , W+T, 0, 0.0, 0.0)
	drawables["arrow_W"] = Arrow(offcolor, oncolor, "W", True, 0, 3 * P, W, -180, 0.0, 0.0)
#VWF
	drawables["arrow_T"] = Arrow(offcolor, oncolor, "T", True, 0, 3.5 * P, T, 0, -0.65, -0.09)
	drawables["arrow_T2"] = Arrow(offcolor, oncolor, "T/2", True, 0, 3 * P, 0.5 * T, 0, -0.35, -0.09)

	drawables["arrow_P"] = Arrow(offcolor, oncolor, "P", True, -0.5 * W, 0, P, 90.0, 0.0, 0.0)
	drawables["arrow_DPrime"] = Arrow(offcolor, oncolor, "D'", True, -0.55 * W, P - D_PRIME, D_PRIME, 90.0, 0.0, 0.0)

	# arrows (radius)
	drawables["arrow_r1"] = Arrow(offcolor, oncolor, "R1", False, p1.x, p1.y, R1, 45.0, -0.27, -0.13)
	drawables["arrow_r2"] = Arrow(offcolor, oncolor, "R2", False, p2.x, p2.y, R2, -135.0, 0.27, 0.12)
	drawables["arrow_r3"] = Arrow(offcolor, oncolor, "R3", False, p3.x, p3.y, R3, -45.0, -0.05,0.2)
	drawables["arrow_ps_p1"] = Arrow(offcolor, oncolor, "R1", False, ps.x, ps.y, R1, -105.0, -0.05, 0.3)
	drawables["arrow_p3"] = Arrow(offcolor, oncolor, "", False, T / 2, p3.y, T / 2 - p3.x, 150.0, 0.0, 0.0)

	# arrows
	drawables["arrow_r1_layout"] = Arrow(offcolor, oncolor, "R1", False, pg.x, pg.y, R1, 180.0 + theta_g - 10.0, 0.0, 0.0)
	drawables["arrow_r2_layout"] = Arrow(offcolor, oncolor, "R2", False, pg.x, pg.y, R2, theta_g + 10.0, -0.4, -0.1)

	# clines
	drawables["cline_L"] = CLine(offcolor, oncolor, "L", 0, 0, theta_g, 0.035, 0.040)

	# arcs
	drawables["arc_v1"] = Arc(offcolor, oncolor, "V1", pg.x, pg.y, R1, 180.0 + theta_g - 15.0, 180.0 + theta_g + 15.0)
	drawables["arc_v2"] = Arc(offcolor, oncolor, "V2", pg.x, pg.y, R2, theta_g - 15.0, theta_g + 15.0)
	drawables["arc_ps_p1"] = Arc(offcolor, oncolor, "ps_p1", ps.x, ps.y, R1, -90 - slope - 15.0, -90 - slope + 15.0)

	try:
		shutil.rmtree(outdir)
	except:
		print("Warning: %s not found" % (outdir))
	
	try:
		os.mkdir(outdir)
	except:
		print("Warning: unable to create %s" % (outdir))

	for key, value in figs.items():
		Draw(drawables, value, outdir + "/" + key + ".tikz")


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
		"-o",
		"--outdir",
		default=default_outdir,
		help="[default={}]".format(str(default_outdir)) + " Output directory.  For example -o \"../figures\""
	)

	parser.add_argument(
		"-s",
		"--slope",
		default=default_slope,
		help="[default={}]".format(str(default_slope)) + " Select tread slope angle, 0.0 <= degrees <= 3.0.  For example -s 2.5"
	)
	
	args = parser.parse_args()
	draw(int(args.code), float(args.slope), str(args.outdir))


# The main entry point for commandline application.
if __name__ == "__main__":
	main()