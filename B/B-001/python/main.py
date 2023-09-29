import json
from argparse import ArgumentParser
from common import *
from keys import *
from data import *
from rp25 import *

default_code = 110
default_slope = 3.0

def main():
	###
	# Handle args
	###
	parser = ArgumentParser(
		prog="RP-25 Calculator",
		description="vwf todo",
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

	# Todo, validate args

	###
	# Input
	###
	input = data[int(args.code)]
	input[alpha] = {value: int(args.slope), unit: degrees}

	###
	# Calculations
	###
	output = calculate(
		input[alpha][value],
		input[T][value], 
		input[P][value],
		input[R1][value],
		input[R2][value],
		input[R3][value]
	)

	###
	# Outputs
	###
	print("--- INPUTS ---")
	print(json.dumps(input, indent=2))
	print("--- OUTPUTS ---")
	print(json.dumps(output, indent=2))


main()
