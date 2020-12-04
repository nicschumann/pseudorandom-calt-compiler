# Pseudorandom Contextual Alternate Compiler

If you give it a set of variations for a set of glyphs standard forms in your typeface, this python script will compile an opentype calt feature that "randomizes" the appearance of a glyph across a set of alternates in the typeface that you specify.

In December 2020, I hacked this together based on a request from Cem Eskinazi. The work is closely based on Tal Leming's "quantum pseudorandom opentype" feature. You can read the idea, context, and Tal's implementation [here](https://opentypecookbook.com/common-techniques/) towards the bottom of the page. Thanks Tal, for such a thorough intro to OpenType Features, and this cool idea. To be 100% clear: I didn't come up for the idea for this randomization strategy; I just made a compiler that makes it easier to write, and gives you some parameters to play with.

This script was designed to output a feature that could be copied and pasted into Glyphs.app's feature editor (specifically for the calt feature). You can also use it from the command line, but you need to specify a complete list of the glyphs in your typeface for the script to work properly.

The source code has plenty of comments and a description of which things you can change, so take a look at `compiler.py` for more detail.
