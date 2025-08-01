#!/bin/bash

# Run this inside developer container.

#rm *.pdf *.log *.dvi *.aux
latex -output-format=pdf C-003.tex
