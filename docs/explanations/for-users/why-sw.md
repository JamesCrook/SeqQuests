# Why Smith-Waterman alignment?

SW held up as 'better than word based methods', because it allows gaps.

However... SW does not handle rearrangement well, and we need to be aware that repetition can be step in rearrangement. In real proteins an 'active site' or binding site can move, despite the general fold of the protein being preserved! The general fold may be determining protein-protein interactions, whereas a specific epitope may be binding to a small molecule. 

* Danger of taking highly conserved proteins as the only model for how proteins change.