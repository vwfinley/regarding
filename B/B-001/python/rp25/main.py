from argparse import ArgumentParser
import json

from rp25 import *

default_code = 110
default_slope = 3.0

def main():
	###
	# Handle args
	###
	parser = ArgumentParser(
		prog="rp25",
		description="Wheel contour calculator for NMRA RP-25 (rev. July 2009) contours.",
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

	# vwf Todo, validate args

	# Call core routine.
	result = rp25(int(args.code), float(args.slope))

	###
	# Display results
	###
	print("--- INPUTS ---")
	print(json.dumps(result[inputs], indent=2))
	print("--- OUTPUTS ---")
	print(json.dumps(result[outputs], indent=2))

# The main entry point for commandline application.
main()