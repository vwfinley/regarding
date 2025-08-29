#!/bin/bash

# Script to run texlive container and generate a pdf from TeX source file.
# To run this from host call: ./build.sh
# The script expects there to be a file named main.tex.
# The generated .pdf will be placed in a directory named output.

IMAGE=ghcr.io/vwfinley/texlive_dev:latest
INFILE=main
OUTDIR=output
OUTFILE=${PWD##*/}

mkdir $OUTDIR

docker run --rm -it -v $(pwd):/workspace $IMAGE latex -output-format=pdf -output-directory=$OUTDIR $INFILE.tex

pushd $OUTDIR
mv $INFILE.pdf $OUTFILE.pdf
popd