#!/bin/bash

# Run this from host.

#rm *.pdf *.log *.dvi *.aux
docker run --rm -it -v $(pwd):/workspace c186cd34cd9b latex -output-format=pdf C-003.tex