#!/bin/bash

# Run this from host.
INFILE=main
OUTDIR=output
OUTFILE=C-003

#rm *.pdf *.log *.dvi *.aux


mkdir $OUTDIR
docker run --rm -it -v $(pwd):/workspace c186cd34cd9b latex -output-format=pdf -output-directory=$OUTDIR $INFILE.tex
pushd $OUTDIR
mv $INFILE.pdf $OUTFILE.pdf
popd
