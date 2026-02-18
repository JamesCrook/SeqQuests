# Molam — Design Insights & Feature Summary

**Core philosophy:** Molam's representations are not separate plot types but settings — the same continuous morphable ribbon viewed differently. Helical wheel, cylinder side view, and topology diagram are orientations and parameters, not modes.

**What existing 3D viewers obscure:**
- Helix directionality (parallel vs antiparallel)
- Axial stacking of sidechains along a helix (glycan clustering, repeat motifs)
- Interface packing between helix pairs and strand pairs
- The connection between 2D topology diagrams and 3D structure
- Internal repeats and correlated substitutions across homologs
- Prosthetic groups as functional units rather than atom clouds

**Interaction geometry:** For parallel/antiparallel helix pairs the relevant visualisation variable is controlled angular perturbation around that axis, not gross rotation. Small tilts reveal different information; the viewer should be gimbal-locked to the substructure axis, not the world origin.

**Selection inversion:** The 3D view is a poor selection interface (occlusion, depth ambiguity). The topology diagram is unambiguous — every substructure is a discrete, labelled, non-occluded symbol. The topology view should serve as the *navigation interface* for the 3D view, not an alternative to it.

**Ribbons are reusable:** The hard problem (continuous, orientation-preserving, morphable ribbons) is solved once and applies to metabolic diagrams, topology diagrams, and sequence markup — not just protein structure.

---

## Features

### Ribbon & Display
[x] Single rectangular cross-section ribbon throughout; no forced mode switching at helix/sheet boundaries
[x] Adjustable smoothing: from undulating beta sheets → Richardson-style → axis-centred helices
[ ] Morphing between conformational states

## Ribbon width / thickness
[ ] Varying the ribbon width can give us classical arrow heads as a formula, namely sawtooth function. A paramaterised function allows us to also show arrow heads mid-sheet, for a long sheet, or repeating barbs.
[ ] Double ribbons. One ribbon standard non varying, acting as a reference, one ribbon with varying parameters to carry the data.

### Colouring & Annotation
[x] Half-half bond colouring with adjustable boundary (colour by lesser/greater atomic number)
[x] Aromatic bonds pink-tinted, adjustable to full
[ ] **Colour/Size by chain distance** along helix/sheet to show chain direction, per substructure, not end-to-end
[ ] **Colour/Size by atomic distance** to chosen residues. Show on topology diagram too.
[ ] **Per-residue-type atom scaling** (e.g. enlarged sulphur atoms in cysteines to show disulphide bridges)

### Topology Morph
[ ] **Topology morph:** animate from 3D cartoon to 2D Richardson topology diagram
[ ] **Topology diagram as navigation UI:** click cylinder/arrow to select helix/strand in 3D; click pair to snap to interface axis view; topology stays visible alongside 3D view

### Feature Morph
[ ] **Feature map morph:** animate from 3D cartoon to linear sequence with featute-table items marked up.

### Cataloue Browsing
[ ] **Catalogue/browser for topology diagrams:** query by diagram similarity; find proteins sharing local topological arrangement regardless of sequence
[ ] **Fold family browser:** load family; rotate all members together; consensus ghost overlay; deviation = functional interest

### Structural Dissection
[ ] **Wedge/slab slicing:** arbitrary plane, membrane-normal plane, or distance-from-axis (coring)
[ ] Slice face shows packing density; cavities and defects visible directly

### Substructure Zoom In
[ ] **Helix axis view / slab mode:** look down helix axis with controllable depth slab; peel through turns one ring of sidechains at a time; numerical angle input for reproducible views
[ ] **Substructure-locked rotation:** gimbal locked to selected helix/sheet axis; rock/rotate with settable angle parameters; depth slab controlled independently
[ ] **Local Distance matrix display:** sequence vs sequence coloured by Cα distance; internal repeats appear as diagonal stripes for visual pattern recognition
[ ] Backbone carbonyl orientation runs: detect potential ion-binding geometry without prior knowledge of bound ion

### Prosthetic Groups
[ ] Well-known groups (haem, Fe-S, FAD, cobalamin) rendered schematically: active parts prominent, scaffold subdued
[ ] Fe-S clusters shown as coordination polyhedra with coordinating residues explicit
[ ] Prosthetic group level-of-detail setting independent of protein representation

### Comparative & Sequence Features
[ ] **Dual display tracking:** select ranges on pairwise alignment; view simultaneously in two structures
[ ] **Indel and gap highlighting:** gaps flagged in alignment; corresponding loops prominent in 3D


