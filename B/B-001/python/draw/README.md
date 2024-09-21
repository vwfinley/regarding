Usage: ./build.sh

Generates figures for the B-001 article.

Calls the figure.py python script to output Tikz drawings for the figures in the article.

You will find the figures in a series of .tikz files located in the output directory that gets created.

First the figure.py python script calls the rp25/main.py script to calculate the critical points for the code=110, slope=3.0 degs wheel contour.

Next figure.py uses the critical points to write Tikz commands to a text file.

The text files that get written have a .tikz extension and can be opened with a Tikz viewer.

The .tikz files can also be ingested into a LaTeX document and rendered.
