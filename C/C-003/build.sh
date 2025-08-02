#!/bin/bash

# Run this inside developer container.
INFILE=main
OUTDIR=output
OUTFILE=C-003

#rm *.pdf *.log *.dvi *.aux

mkdir $OUTDIR
latex -output-format=pdf -output-directory=$OUTDIR $INFILE.tex
pushd $OUTDIR
mv $INFILE.pdf $OUTFILE.pdf
popd

