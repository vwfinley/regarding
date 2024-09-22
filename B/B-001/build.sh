#!/bin/bash

# To build the article simple run: ./build.sh

cd python/draw
rm -rf output
./build.sh

cd -
cd python/table
rm -rf output
./build.sh

cd -

rm *.pdf
pdflatex B-001.tex
