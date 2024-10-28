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
#default_slope = 15.0
region = 1
scale = 45
detail_scale = 70
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
		self.off = self.on = "\\end{scope}\n" + "\\end{tikzpicture}\n"


class Clip(Drawable):
	def __init__(self, left: float, top: float, w: float, h: float):
		s = "\\clip ({:.5f}, {:.5f}) rectangle ({:.5f}, {:.5f});\n"
		self.off = ""
		self.on = s.format(left, top, w, h)

class XAxis(Drawable):
	def __init__(self, offcolor: str, oncolor: str, x1: float, x2: float):
		s = "\\draw[{}, -{{latex[scale=1.5]}}] ({:.5f}, 0) -- ({:.5f}, 0)  node [right] {{$x$}};\n"
		self.off = s.format(offcolor, x1, x2)		
		self.on = s.format(oncolor, x1, x2)		

class YAxis(Drawable):
	def __init__(self, offcolor: str, oncolor: str, y1: float, y2: float):
		s = "\\draw[{}, -{{latex[scale=1.5]}}] (0, {:.5f}) -- (0, {:.5f})  node [above] {{$y$}};\n"
		self.off = s.format(offcolor, y1, y2)
		self.on = s.format(oncolor, y1, y2)

class Line(Drawable):
	def __init__(self, offcolor: str, oncolor: str, label: str, x1: float, y1: float, x2: float, y2: float, x_label_offset: float, y_label_offset: float):
		s = "\\draw[{}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f}) node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"
		self.off = s.format(offcolor, x1, y1, x2, y2, x_label_offset, y_label_offset, label)	
		self.on = s.format(oncolor, x1, y1, x2, y2, x_label_offset, y_label_offset, label)		

class CLine(Line):
	def __init__(self, offcolor: str, oncolor: str, label: str, x: float, y: float, angle: float, r1: float, r2: float):
		cos = math.cos(math.radians(angle))
		sin = math.sin(math.radians(angle))
		dx1 = r1 * cos
		dy1 = r1 * sin
		dx2 = r2 * cos
		dy2 = r2 * sin
		super().__init__(offcolor, oncolor, label, x - dx1, y - dy1, x + dx2, y + dy2, 0.0, 0.0)

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
	def __init__(self, offcolor: str, oncolor: str, label: str, atstart: bool, x: float, y: float, radius: float, start_angle: float, end_angle: float, x_label_offset: float, y_label_offset: float):
		if atstart:
			s = "\\draw[{0}, {{latex[scale=0.75]}}-{{latex[scale=0.75]}}] ([shift=({5:.5f} : {4:.5f})] {2:.5f},{3:.5f}) arc ({5:.5f} : {6:.5f} : {4:.5f}) node [shift={{({7:.5f}, {8:.5f})}}] {{${1}$}};\n"
		else:
			s = "\\draw[{0}, {{latex[scale=0.75]}}-] ([shift=({5:.5f} : {4:.5f})] {2:.5f},{3:.5f}) arc ({5:.5f} : {6:.5f} : {4:.5f}) node [shift={{({7:.5f}, {8:.5f})}}] {{${1}$}};\n"
		self.off = s.format(offcolor, label, x, y, radius, start_angle, end_angle, x_label_offset, y_label_offset)
		self.on = s.format(oncolor, label, x, y, radius, start_angle, end_angle, x_label_offset, y_label_offset)

class Arrow(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, atstart: bool, x: float, y: float, length: float, angle: float, x_label_offset: float, y_label_offset: float):
		dx = length * math.cos(math.radians(angle))
		dy = length * math.sin(math.radians(angle))
		if atstart:
			s = "\\draw[{}, {{latex[scale=0.75]}}-{{latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f}) node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"
		else:
			s = "\\draw[{}, -{{latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"

		self.off = s.format(offcolor, x, y, x + dx, y + dy, x_label_offset, y_label_offset, label)
		self.on = s.format(oncolor, x, y, x + dx, y + dy, x_label_offset, y_label_offset, label)

class RArrow(Drawable): 
	def __init__(self, offcolor: str, oncolor: str, label: str, atstart: bool, x: float, y: float, x2: float, y2: float, x_label_offset: float, y_label_offset: float):
		if atstart:
			s = "\\draw[{}, {{latex[scale=0.75]}}-{{latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f}) node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"
		else:
			s = "\\draw[{}, -{{latex[scale=0.75]}}] ({:.5f}, {:.5f}) -- ({:.5f}, {:.5f})  node [shift={{({:.5f}, {:.5f})}}] {{${}$}};\n"

		self.off = s.format(offcolor, x, y, x2, y2, x_label_offset, y_label_offset, label)
		self.on = s.format(oncolor, x, y, x2, y2, x_label_offset, y_label_offset, label)



figs3deg = {
	"fig1": {
		"begin": State.On,
		"clip": State.On,
		"full_clip": State.Off,

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

#		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,

		"end": State.On
	},
	"fig2": {
		"begin": State.On,
		"clip": State.On,
		"full_clip": State.Off,

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

#		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig3": {
		"begin": State.On,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig4": {
		"begin": State.On,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig5": {
		"begin": State.Off,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig6": {
		"begin": State.Off,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig7": {
		"begin": State.Off,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig8": {
		"begin": State.Off,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig9": {
		"begin": State.Off,
		"clip": State.On,
		"full_clip": State.Off,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"end": State.On
	},
	"fig10": {
		"begin": State.Off,
		"clip": State.Off,
		"full_clip": State.On,


		"x_axis": State.On,
		"y_axis": State.On,

		"line_P": State.Off,
		"line_Dprime": State.Off,
#		"line_false_x_axis": State.Off,
		"line_p2_p3":  State.Off,

		"line_T": State.Off,
		"line_T2": State.Off,
		"line_Tbase_dim": State.Off,
		"line_T_dim": State.Off,
		"line_T2_dim": State.Off,

		"line_T_full": State.On,
		"line_W": State.On,

		"line_slope": State.Off,
		"line_ps_p1": State.Off,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.On,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

		"arc_c1": State.On,
		"arc_c2": State.On,
		"arc_c3": State.On,
		"arc_ps_p1": State.Off,
		"arc_p3": State.Off,

		"arrow_NPrime": State.Off,
		"arrow_W": State.Off,
		"arrow_T": State.Off,
		"arrow_T2": State.Off,
		"arrow_P": State.Off,
		"arrow_DPrime": State.Off,

		"arrow_r1": State.Off,
		"arrow_r2": State.Off,
		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.Off,
#		"arrow_p3": State.Off,

		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

#		"arc_v1": State.Off,
		"arc_v2": State.Off,

		"arc_fillet_0deg": State.On,
		"arc_fillet_3deg": State.On,

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

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

		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
		"pointmark_pd": State.On,
		"pointmark_p1": State.On,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"end": State.On
	}
}

figs15deg = {

	"fig11a": {
		"detail_begin": State.On,
		"detail_clip": State.On,

#		"x_axis": State.On,
#		"y_axis": State.On,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

		"line_ps_p1_horizontal": State.On,
		"line_ps_p1_vertical": State.On,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope_detail": State.Off,
#		"line_ps_p1": State.On,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.Off,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

# VWF
#		"arc_slope": State.On,
#		"arc_slope_upper_15deg": State.Off,
		"arc_slope_inside_15deg": State.On,
#		"arc_slope_lower_15deg": State.Off,
		"arc_slope_theta_s_left": State.On,
		"arc_slope_theta_s_right": State.On,

#		"arc_c1": State.On,
#		"arc_c2": State.On,
#		"arc_c3": State.On,
#		"arc_ps_p1": State.On,

#		"arrow_NPrime": State.Off,
#		"arrow_W": State.Off,
#		"arrow_T": State.Off,
#		"arrow_T2": State.Off,
#		"arrow_P": State.Off,
#		"arrow_DPrime": State.Off,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.On,

#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

		"arrow_r1_ps_p1": State.On,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,

#		"pointmark_pg": State.On,
		"pointmark_ps": State.On,
#		"pointmark_pd": State.On,
		"pointmark_p1_detail": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},

	"fig11b": {
		"detail_begin": State.On,
		"detail_clip": State.On,

#		"x_axis": State.On,
#		"y_axis": State.On,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

#		"line_ps_p1_horizontal": State.Off,
#		"line_ps_p1_vertical": State.Off,
		"line_pg_horizontal": State.Off,

		"line_p1_pg_horizontal": State.On,
		"line_p1_pg_vertical": State.On,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope_detail": State.Off,
#		"line_ps_p1": State.On,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.Off,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

# VWF
#		"arc_slope": State.On,
#		"arc_slope_upper_15deg": State.Off,
#		"arc_slope_lower_15deg": State.Off,

#		"arc_c1": State.On,
#		"arc_c2": State.On,
#		"arc_c3": State.On,
#		"arc_ps_p1": State.On,

		"arc_slope_theta_g_p1_top": State.On,
		"arc_slope_theta_g_p1_bottom": State.On,

#		"arrow_NPrime": State.Off,
#		"arrow_W": State.Off,
#		"arrow_T": State.Off,
#		"arrow_T2": State.Off,
#		"arrow_P": State.Off,
#		"arrow_DPrime": State.Off,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.On,

#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

		"arrow_r1_ps_p1": State.Off,
		"arrow_r1_p1_pg": State.On,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,

		"pointmark_pg_detail": State.On,
		"pointmark_ps": State.Off,
#		"pointmark_pd": State.On,
		"pointmark_p1_detail": State.On,
#		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},










	"fig11c": {
		"detail_begin": State.On,
		"detail_clip": State.On,

#		"x_axis": State.On,
#		"y_axis": State.On,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

#		"line_ps_p1_horizontal": State.Off,
#		"line_ps_p1_vertical": State.Off,
		"line_pg_horizontal": State.Off,

#		"line_p1_pg_horizontal": State.On,
#		"line_p1_pg_vertical": State.On,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope_detail": State.Off,
#		"line_ps_p1": State.On,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.Off,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

# VWF
#		"arc_slope": State.On,
#		"arc_slope_upper_15deg": State.Off,
#		"arc_slope_lower_15deg": State.Off,

#		"arc_c1": State.On,
#		"arc_c2": State.On,
#		"arc_c3": State.On,
#		"arc_ps_p1": State.On,

#		"arrow_NPrime": State.Off,
#		"arrow_W": State.Off,
#		"arrow_T": State.Off,
#		"arrow_T2": State.Off,
#		"arrow_P": State.Off,
#		"arrow_DPrime": State.Off,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.On,

#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

		"arrow_r1_ps_p1": State.Off,
		"arrow_r1_p1_pg": State.Off,
		"arrow_r2_pg_p2": State.On,

#		"arc_v1": State.Off,
#		"arc_v2": State.Off,

		"pointmark_pg_detail": State.On,
		"pointmark_ps": State.Off,
#		"pointmark_pd": State.On,
		"pointmark_p1_detail": State.Off,
		"pointmark_p2": State.On,
#		"pointmark_p3": State.On,

		"end": State.On
	},








	"fig11d": {
		"detail_begin": State.On,
		"full_detail_clip": State.On,

#		"x_axis": State.On,
#		"y_axis": State.On,

		"line_P": State.Off,
#		"line_Dprime": State.Off,

#		"line_ps_p1_horizontal": State.Off,
#		"line_ps_p1_vertical": State.Off,
		"line_pg_horizontal": State.Off,

#		"line_p1_pg_horizontal": State.On,
#		"line_p1_pg_vertical": State.On,

#		"line_T": State.Off,
#		"line_T2": State.Off,
#		"line_W": State.Off,

		"line_slope_detail": State.Off,
#		"line_ps_p1": State.On,
		"line_slope_corner_1": State.Off,
		"line_slope_corner_2": State.Off,

#		"centermark_p1": State.Off,
#		"centermark_p2": State.Off,
#		"centermark_p3": State.Off,

# VWF
#		"arc_slope": State.On,
#		"arc_slope_upper_15deg": State.Off,
#		"arc_slope_lower_15deg": State.Off,

#		"arc_c1": State.On,
#		"arc_c2": State.On,
#		"arc_c3": State.On,
#		"arc_ps_p1": State.On,

#		"arrow_NPrime": State.Off,
#		"arrow_W": State.Off,
#		"arrow_T": State.Off,
#		"arrow_T2": State.Off,
#		"arrow_P": State.Off,
#		"arrow_DPrime": State.Off,

#		"arrow_r1": State.Off,
#		"arrow_r2": State.Off,
#		"arrow_r3": State.Off,
#		"arrow_ps_p1": State.On,

#		"cline_L": State.Off,

#		"arrow_r1_layout": State.Off,
#		"arrow_r2_layout": State.Off,

		"arrow_r1_ps_p1": State.Off,
		"arrow_r1_p1_pg": State.Off,
		"arrow_r2_pg_p2": State.Off,

		"rarrow_p2_pd": State.On,
		"rarrow_p2_p3": State.On,


#		"arc_v1": State.Off,
#		"arc_v2": State.Off,

		"pointmark_pg_detail": State.Off,
		"pointmark_ps": State.Off,
		"pointmark_pd": State.On,
		"pointmark_p1_detail": State.Off,
		"pointmark_p2": State.On,
		"pointmark_p3": State.On,

		"end": State.On
	}









}

def RotatePoint(x: float, y: float, theta_rad: float):
	x1 = x * math.cos(theta_rad) - y * math.sin(theta_rad)
	y1 = x * math.sin(theta_rad) + y * math.cos(theta_rad)
	return (x1, y1)

def CalcFillet(radius: float, theta_deg: float, rot_deg: float):
	theta_rad = math.radians(theta_deg)
	rot_rad = math.radians(rot_deg)

	alpha_rad = theta_rad / 2
	dx = radius / math.sin(alpha_rad)
	d = radius / math.tan(alpha_rad)
	
	Cx = dx
	Cy = 0
	Px = d * math.cos(alpha_rad)
	Py = d * math.sin(alpha_rad)
	P1x = Px
	P1y = -Py
	
	C = RotatePoint(Cx, Cy, rot_rad)
	P = RotatePoint(Px, Py, rot_rad)
	P1 = RotatePoint(P1x, P1y, rot_rad)

	return (C, P, P1)


def generate_drawables(code: int, slope: float) -> dict[str, Drawable]:
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
	drawables["detail_begin"] = Begin(region, detail_scale)
	drawables["end"] = End()
	drawables["clip"] = Clip(-0.021, -0.030, 0.05, 0.05)
	drawables["full_clip"] = Clip(-0.1, -0.030, 0.05, 0.05)
#vwf
	drawables["detail_clip"] = Clip(-0.021, -0.006, 0.021, 0.012)
	drawables["full_detail_clip"] = Clip(-0.021, -0.015, 0.021, 0.012)

	drawables["x_axis"] = XAxis(offcolor, oncolor, -W - 0.005, T + 2 * overhang)
	drawables["y_axis"] = YAxis(offcolor, oncolor, P - D_PRIME - 2 * overhang , P + 2 * overhang)

	# h lines
	left = -W - overhang
	right = T + overhang
	drawables["line_P"] = Line(offcolor, oncolor, "", -W - 0.01, P, right, P, 0.0, 0.0)
	drawables["line_false_x_axis"] = Line(offcolor, oncolor, "", -1, 0, 1, 0, 0.0, 0.0)
	drawables["line_Dprime"] = Line(offcolor, oncolor, "", -W - 0.01, P - D_PRIME, right, P - D_PRIME, 0.0, 0.0)

	drawables["line_p2_p3"] = Line(offcolor, oncolor, "", p2.x - 0.006, p2.y, p3.x + 0.006, p3.y, 0.0, 0.0)

	drawables["line_ps_p1_horizontal"] = Line(offcolor, oncolor, "x_s", ps.x, p1.y, p1.x, p1.y, 0.15, -0.08)
	drawables["line_pg_horizontal"] = Line(offcolor, oncolor, "", pg.x - 0.1, pg.y, pg.x + 0.1, pg.y, 0.0, 0.0)

	drawables["line_p1_pg_horizontal"] = Line(offcolor, oncolor, "x_g", p1.x, p1.y, pg.x, p1.y, -0.40, -0.09)


	# v lines
	top = P + overhang
	bottom = P - D_PRIME - overhang
	drawables["line_T"] = Line(offcolor, oncolor, "", T, bottom, T, top, 0.0, 0.0)
	drawables["line_T2"] = Line(offcolor, oncolor, "", T / 2, bottom, T / 2, top, 0.0, 0.0)
	drawables["line_Tbase_dim"] = Line(offcolor, oncolor, "", 0, 2.9 * P, 0, 3.6 * P, 0.0, 0.0)
	drawables["line_T_dim"] = Line(offcolor, oncolor, "", T, 3.4 * P, T, 3.6 * P, 0.0, 0.0)
	drawables["line_T2_dim"] = Line(offcolor, oncolor, "", T / 2, 2.9 * P, T / 2, 3.1 * P, 0.0, 0.0)

	drawables["line_T_full"] = Line(offcolor, oncolor, "", T, 0, T, 4.5 * P, 0.0, 0.0)
	drawables["line_W"] = Line(offcolor, oncolor, "", -W, P, -W, 4.5 * P, 0.0, 0.0)

	drawables["line_ps_p1_vertical"] = Line(offcolor, oncolor, "y_s", ps.x, ps.y, ps.x, p1.y, 0.1, 0.4)

	drawables["line_p1_pg_vertical"] = Line(offcolor, oncolor, "y_g", pg.x, p1.y, pg.x, pg.y, 0.1, -0.15)

	# diag lines
	slope1 =  math.radians(0.0 - slope)
	slope2 = math.radians(180.0 - slope)
	l1 = 0.8 * T
	l2 = 0.9 * W
	x1 = l1 * math.cos(slope1)
	y1 = l1 * math.sin(slope1)
	x2 = l2 * math.cos(slope2)
	y2 = l2 * math.sin(slope2)
	drawables["line_slope"] = Line(offcolor, oncolor, "slope (\\theta_s)", ps.x + x1, ps.y + y1, ps.x + x2, ps.y + y2, 0.0, 0.0)  # Tread slope

	l1 = 0.4 * T
	l2 = 0.9 * W
	x1 = l1 * math.cos(slope1)
	y1 = l1 * math.sin(slope1)
	x2 = l2 * math.cos(slope2)
	y2 = l2 * math.sin(slope2)
	drawables["line_slope_detail"] = Line(offcolor, oncolor, "slope (\\theta_s)", ps.x + x1, ps.y + y1, ps.x + x2, ps.y + y2, 0.0, 0.0)  # Tread slope


	len = 0.001
	slope1 =  math.radians(180.0 - slope)
	slope2 = math.radians(135.0 - slope)
	x1 = len * 1.0 * math.cos(slope1)
	y1 = len * 1.0 * math.sin(slope1)
	x2 = len * 1.414 * math.cos(slope2)
	y2 = len * 1.414 * math.sin(slope2)
	drawables["line_slope_corner_1"] = Line(offcolor, oncolor, "", ps.x - x1, ps.y - y1, ps.x - x2, ps.y - y2, 0.0, 0.0)  # 

	slope3 = math.radians(90.0 - slope)
	x3 = len * 1.0 * math.cos(slope3)
	y3 = len * 1.0 * math.sin(slope3)
	drawables["line_slope_corner_2"] = Line(offcolor, oncolor, "", ps.x - x2, ps.y - y2, ps.x - x3, ps.y - y3, 0.0, 0.0)  # 

	slope1 =  math.radians(90.0 - slope)
	slope2 = math.radians(270.0 - slope)
	x1 = 0.5 * R1 * math.cos(slope1)
	y1 = 0.5 * R1 * math.sin(slope1)
	x2 = 1.5 * R1 * math.cos(slope2)
	y2 = 1.5 * R1 * math.sin(slope2)
	drawables["line_ps_p1"] = Line(offcolor, oncolor, "", ps.x + x1, ps.y + y1, ps.x + x2, ps.y + y2, 0.0, 0.0)  # ps->p1 line

	# centermarks
	drawables["centermark_p1"] = Centermark(offcolor, oncolor, p1.label, p1.x, p1.y)
	drawables["centermark_p2"] = Centermark(offcolor, oncolor, p2.label, p2.x, p2.y)
	drawables["centermark_p3"] = Centermark(offcolor, oncolor, p3.label, p3.x, p3.y)

	# pointmarks
	drawables["pointmark_pg"] = Pointmark(offcolor, oncolor, pg.label, pg.x, pg.y, 0.14, -0.09)
	drawables["pointmark_ps"] = Pointmark(offcolor, oncolor, ps.label, ps.x, ps.y, 0.13, -0.09)
	drawables["pointmark_pd"] = Pointmark(offcolor, oncolor, pd.label, pd.x, pd.y, 0.13, -0.07)
	drawables["pointmark_p1"] = Pointmark(offcolor, oncolor, p1.label, p1.x, p1.y, 0.13, -0.08)
	drawables["pointmark_p2"] = Pointmark(offcolor, oncolor, p2.label, p2.x, p2.y, 0.13, -0.07)
	drawables["pointmark_p3"] = Pointmark(offcolor, oncolor, p3.label, p3.x, p3.y, -0.14, 0)

	drawables["pointmark_pg_detail"] = Pointmark(offcolor, oncolor, pg.label, pg.x, pg.y, 0.07, 0.11)
	drawables["pointmark_p1_detail"] = Pointmark(offcolor, oncolor, p1.label, p1.x, p1.y, -0.08, -0.08)


	# arcs
	drawables["arc_c1"] = Arc(offcolor, oncolor, "c1", p1.x, p1.y, R1, -30, 115)
	drawables["arc_c2"] = Arc(offcolor, oncolor, "c2", p2.x, p2.y, R2, 180, 285)
	drawables["arc_c3"] = Arc(offcolor, oncolor, "c3", p3.x, p3.y, R3, 255, 360)
	drawables["arc_p3"] = Arc(offcolor, oncolor, "p3",  T / 2, p3.y,  T / 2 - p3.x, 140, 240)

	arc_slope_radius = 0.023
	drawables["arc_slope_upper"] = ArcArrow(offcolor, oncolor, "", False, ps.x, ps.y,  arc_slope_radius, 0, 10, 0, 0)
	drawables["arc_slope_lower"] = ArcArrow(offcolor, oncolor, "slope (\\theta_s)", False, ps.x, ps.y, arc_slope_radius, 360 - slope, 360 - slope - 10, 0, 0)

#vwf
	drawables["arc_slope_inside_15deg"] = ArcArrow(offcolor, oncolor, "\\theta_s", True, ps.x, ps.y,  0.01, -slope, 0, 0.1, -0.1)

	arc_slope_radius = 0.004
	drawables["arc_slope_theta_s_left"] = ArcArrow(offcolor, oncolor, "\\theta_s", False, ps.x, ps.y,  arc_slope_radius, 270 - slope, 270 - slope - 20, -0.08, 0.02)
	drawables["arc_slope_theta_s_right"] = ArcArrow(offcolor, oncolor, "", False, ps.x, ps.y, arc_slope_radius, 270, 270 + 20, 0, 0)

	drawables["arc_slope_theta_g_p1_top"] = ArcArrow(offcolor, oncolor, "\\theta_g", False, p1.x, p1.y,  arc_slope_radius, 0 + theta_g, 0 + theta_g + 20, -0.07, 0.03)
	drawables["arc_slope_theta_g_p1_bottom"] = ArcArrow(offcolor, oncolor, "", False, p1.x, p1.y, arc_slope_radius, 0, -20, 0, 0)


	# arrows (layout)
	drawables["arrow_NPrime"] = Arrow(offcolor, oncolor, "N'", True, -W, 4.0 * P , W+T, 0, -2.5, 0.1)
	drawables["arrow_W"] = Arrow(offcolor, oncolor, "W", True, 0, 3.5 * P, W, -180, 1.8, 0.1)
	drawables["arrow_T"] = Arrow(offcolor, oncolor, "T", True, 0, 3.5 * P, T, 0, -0.65, 0.1)
	drawables["arrow_T2"] = Arrow(offcolor, oncolor, "T/2", True, 0, 3 * P, 0.5 * T, 0, -0.35, 0.1)

	drawables["arrow_P"] = Arrow(offcolor, oncolor, "P", True, -1.05 * W, 0, P, 90.0, 0.07, -0.25)
	drawables["arrow_DPrime"] = Arrow(offcolor, oncolor, "D'", True, -1.1 * W, P - D_PRIME, D_PRIME, 90.0, 0.1, -0.6)

	# arrows (radius)
	drawables["arrow_r1"] = Arrow(offcolor, oncolor, "R1", False, p1.x, p1.y, R1, 45.0, -0.27, -0.13)
	drawables["arrow_r2"] = Arrow(offcolor, oncolor, "R2", False, p2.x, p2.y, R2, -135.0, 0.27, 0.12)
	drawables["arrow_r3"] = Arrow(offcolor, oncolor, "R3", False, p3.x, p3.y, R3, -45.0, -0.05,0.2)
	drawables["arrow_ps_p1"] = Arrow(offcolor, oncolor, "R1", False, ps.x, ps.y, R1, -105.0, -0.05, 0.3)
	drawables["arrow_p3"] = Arrow(offcolor, oncolor, "", False, T / 2, p3.y, T / 2 - p3.x, 150.0, 0.0, 0.0)

	# arrows
	drawables["arrow_r1_layout"] = Arrow(offcolor, oncolor, "R1", False, pg.x, pg.y, R1, 180.0 + theta_g - 10.0, 0.0, 0.0)
	drawables["arrow_r2_layout"] = Arrow(offcolor, oncolor, "R2", False, pg.x, pg.y, R2, theta_g + 10.0, -0.4, -0.1)

	drawables["arrow_r1_ps_p1"] = Arrow(offcolor, oncolor, "R1", False, ps.x, ps.y, R1, 270.0 - slope, -0.03, 0.45)
	drawables["arrow_r1_p1_pg"] = Arrow(offcolor, oncolor, "R1", False, p1.x, p1.y, R1, theta_g, -0.50, -0.03)

	drawables["arrow_r2_pg_p2"] = Arrow(offcolor, oncolor, "R2", False, pg.x, pg.y, R2, theta_g, -0.5, -0.22)

	# rarrows
	drawables["rarrow_p2_pd"] = RArrow(offcolor, oncolor, "R2", False, p2.x, p2.y, pd.x, pd.y, 0.2, 0.6)
	drawables["rarrow_p2_p3"] = RArrow(offcolor, oncolor, "?", False, p2.x, p2.y, p3.x, p3.y, 0.2, 0.1)

	# clines
	drawables["cline_L"] = CLine(offcolor, oncolor, "L", 0, 0, theta_g, 0.035, 0.040)

	# arcs
	drawables["arc_v1"] = Arc(offcolor, oncolor, "V1", pg.x, pg.y, R1, 180.0 + theta_g - 15.0, 180.0 + theta_g + 15.0)
	drawables["arc_v2"] = Arc(offcolor, oncolor, "V2", pg.x, pg.y, R2, theta_g - 13.0, theta_g + 13.0)
	drawables["arc_ps_p1"] = Arc(offcolor, oncolor, "ps_p1", ps.x, ps.y, R1, -90 - slope - 15.0, -90 - slope + 15.0)
	
	# corner fillets
	slopeRads =  math.radians(slope)
	filletRadius = 0.005
	tw = math.fabs(W + ps.x)     # treadwidth (plus ps.x because ps.x is already negative)

	(Cxy, Pxy, P1xy) = CalcFillet(filletRadius, 90.0, 45.0)
	pCorner0deg = Point("pCorner0deg", -W, ps.y)
	pCenter0deg = Point("pCenter0deg", Cxy[0] + pCorner0deg.x, Cxy[1] + pCorner0deg.y)
	pLegX0deg = Point("pLegX0deg", P1xy[0] + pCorner0deg.x, P1xy[1] + pCorner0deg.y)
	pLegY0deg = Point("pLegY0deg", Pxy[0] + pCorner0deg.x, Pxy[0] + pCorner0deg.y)

	drawables["arc_fillet_0deg"] = Arc(offcolor, oncolor, "arc_fillet_0deg", pCenter0deg.x, pCenter0deg.y, filletRadius, 180, 270)

	(Cxy, Pxy, P1xy) = CalcFillet(filletRadius, 90.0 + slope, 90.0 - 0.5 * (90.0 + slope))
	pCorner3deg = Point("pCorner3deg", -W, tw * math.tan(slopeRads) + ps.y);
	pCenter3deg = Point("pCenter3deg", Cxy[0] + pCorner3deg.x, Cxy[1] + pCorner3deg.y)
	pLegX3deg = Point("pLegX3deg", P1xy[0] + pCorner3deg.x, P1xy[1] + pCorner3deg.y)
	pLegY3deg = Point("pLegY3deg", Pxy[0] + pCorner3deg.x, Pxy[0] + pCorner3deg.y)

	drawables["arc_fillet_3deg"] = Arc(offcolor, oncolor, "arc_fillet_3deg", pCenter3deg.x, pCenter3deg.y, filletRadius, 180, 267)

	return drawables


def Draw(drawables: dict, d: dict, filename: str):
	with open(filename, 'w') as f:
		for key, value in d.items():
			f.write(drawables[key].draw(value))

def draw(code: int, slope: float, outdir: str, figures: dict[str, dict[str, State]]):

	#figures =  dict[str, dict[str, State]]

	drawables = generate_drawables(code, slope)

	for key, value in figures.items():
		Draw(drawables, value, outdir + "/" + key + ".tikz")


def create_outdir(outdir: str):
	try:
		shutil.rmtree(outdir)
	except:
		print("Warning: %s not found" % (outdir))
	
	try:
		os.mkdir(outdir)
	except:
		print("Warning: unable to create %s" % (outdir))



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

	create_outdir(str(args.outdir))
	draw(int(args.code), float(args.slope), str(args.outdir), figs3deg)
	draw(int(args.code), 15.0, str(args.outdir), figs15deg)


# The main entry point for commandline application.
if __name__ == "__main__":
	main()
