# Overview

SeqQuests is a sequence analysis package which can be used via a web interface. It runs on Mac hardware.

SeqQuests provides:
* A very fast metal-accelerated Smith-Waterman local similarity search (2 days for 570,000 sequences all-on-all on Mac M4 Pro)
* Methods for making, browsing and reducing an all-on-all Swiss-Prot protein sequence comparison 
* LCARs (Star Trek TNG) inspired web user interface for protein sequence work.

Some preliminary results from using the all-on-all comparison pipeline are included in the repository  in the /findings folder.

SeqQuests was developed for local use rather than for use by many people connecting over the internet. 

# Main Pipeline

* Prepares data files from the database to facilitate searching. SeqQuests will search with the longest protein sequences first and work down to the smallest. This step is about sorting and 'packing' the sequence files. The amino acid similarity table also needs to be prepared.
* Does the all-on-all comparison, taking about 2 days.
* Builds a [tree from the comparisons](./tree.md). This 'picks out' best connections between families. It is not an evolutionary history. It is single linkage cluster analysis to reduce the volume of results whilst still preserviong connections.
* Filters out 'uninteresting' links from the tree
* (now in the web browser) explore those similarities.

# Additional Tools
* Retrieve structures for chosen pairs of proteins
* Align their structures

# Web UI

* Job manager interface for starting, pausing, monitoring and deleting jobs.