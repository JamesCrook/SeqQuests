# Molam Ideas

Molam is a protein molecule viewer that can view both 3D structures and flat 2D domain maps and feature table annotated sequence. 

An unusual feature is that you can smoothly morph from the flat 2D view of sequence, marked up with alpha helices, beta sheets and disordered, to the 3D view. This isn't a true folding pathway, rather it relates the 2D and 3D view. This is most useful when comparing two aligned sequences. It becomes easier to relate the region of homology to the 3D structure.

## Beta Sheet Smoothing

In Jane Richardson's cartoon views of molecules, beta sheets were smoothed out to gently curving ribbons. In actuality the alpha carbon atoms describe an undulating path. In Molam you can adjust the amount of smoothing to make this undulation more or less pronounced. The default, like other protein viewers such as NGL, is to show the undulation. You can then compare undulation in adjacent beta sheets in a barrel. You can see these undulation too from an actual atomic view, but it is easier from the ribbon view. If you want the fully simplified view, a smoothing slider will smooth the ribbons. 

## Alpha Helix Smoothing

Alpha helices are normally drawn with a hollow core to the helix. In fact, at the atomic level, this core is packed - there is no room for a small ion to travel down the helical 'tube'. The tube is more a feature of the simplified representation than an actual conduit.

In Molam you can view the helices in the standard helical representation. You can also 'over smooth' them, to get a twisted-core representation. With over-smoothing the ribbon travels along the centre line of the helix and it twists as it does so, the twist representing the pitch of the ribbon. 

## Sequence <-> Structure Relationships

In Molam you can select regions in a linear protein and see their postions on the 3D model. Moreover you can 'light up' residues in the sequence by distance to the selected residues when folded. This is particularly valuable for understanding correlated changes in multiple sequence alignments.