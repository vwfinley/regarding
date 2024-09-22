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
#region = 1
#scale = 45
#overhang = 0.007


#\begin{center}
#\begin{tabular}{ c c c }
# cell1 & cell2 & cell3 \\ 
# cell4 & cell5 & cell6 \\  
# cell7 & cell8 & cell9    
#\end{tabular}
#\end{center}

def format_point(p: Point) -> str:
    return f'({p.x:.4f}, {p.y:.4f})'

def generate_row(code: int, slope: float) -> str:
    results = rp25(code, slope)
    input = results[inputs]
    output = results[outputs]

#    print("--- INPUTS ---")
#    print(json.dumps(input, indent=2))
#    print("--- OUTPUTS ---")
    # print(json.dumps(output, indent=2))

    N_PRIME = input["N_PRIME"]["value"]
#	T = input["T"]["value"]
#	W = input["W"]["value"]
#	D_PRIME = input["D_PRIME"]["value"]
#	P = input["P"]["value"]
#	R1 = input["R1"]["value"]
#	R2 = input["R2"]["value"]
#	R3 = input["R3"]["value"]
#	slope = input["slope"]["value"]

    pg = format_point(Point("p_g", output["pg"]["x"], output["pg"]["y"]))
    theta_g =  output["theta_g"]["value"]
    ps = format_point(Point("p_s", output["ps"]["x"], output["ps"]["y"]))
    pd = format_point(Point("p_d", output["pd"]["x"], output["pd"]["y"]))
    p1 = format_point(Point("p_1", output["p1"]["x"], output["p1"]["y"]))
    p2 = format_point(Point("p_2", output["p2"]["x"], output["p2"]["y"]))
    p3 = format_point(Point("p_3", output["p3"]["x"], output["p3"]["y"]))
    d_prime =  output["d_prime"]["value"]

    s = f'{code} & {slope:.1f} & {pg} & {theta_g:.4f} & {ps} & {pd} & {p1} & {p2} & {p3} & {d_prime:.4f} \\\\'

    return s
  


def main():
    ###
    # Handle args
    ###
    parser = ArgumentParser(
        prog="figure",
        description="Generate table for B-001.",
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
    s = generate_row(int(args.code), float(args.slope))
    print(s)


# The main entry point for commandline application.
if __name__ == "__main__":
    main()
