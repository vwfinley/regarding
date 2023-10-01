from common import *
from keys import *
from data import *
from calc import *

def rp25(icode: int, fslope: float) -> tuple[dict, dict]:
	###
	# Input
	###
	input = data[icode]
	input[slope] = {value: fslope, unit: degrees}

	###
	# Calculations
	###
	output = calculate(
		input[slope][value],
		input[T][value], 
		input[P][value],
		input[R1][value],
		input[R2][value],
		input[R3][value]
	)

	return (input, output)
