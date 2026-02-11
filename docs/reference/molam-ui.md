# Molam UI

Molam is a new and experimental protein model viewer.

Parameters in the control panel give considerable flexibility into how exactly a molecule is displayed

----

## Control point smoothing

The red and green control points are used in the algorithm for smooth ribbons.
* The red control points are placed at alpha carbon atom positions initially. However, with smoothing they migrate towards the centre line of alpha helices and beta sheets. 
* The green control points are drawn half way between the red ones. The algorithm draws smooth circular arcs between red and green.

The smoothing at 0.5 uncrinkles beta sheets so that they do not undulate. At 0.75 it straightens alpha helices, and the ribbon line will run along the axis and twist as it does so.

## Half colour

The half colour slider affects the colouring of bonds. At 0.5 the bond is coloured half and half, equally by the two atom colours. At 1.0 it is coloured by the higher atomic number atom. At 0.0 it is coloured by the lower atomic number atom.

## Pink Links

Bonds in aromatics will be pink coloured when this slider is slid to 1.0.