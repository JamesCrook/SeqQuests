# SeqQuests

SeqQuests is a sequence analysis package. The SeqQuests repo also contains datasets in /findings/, produced using this software.

SeqQuests provides:
* A fast metal-accelerated Smith-Waterman local similarity search (2 days for 570,000 sequences all-on-all on Mac M4 Pro)
* Tooling for making, browsing and reducing an all-on-all Swiss-Prot protein sequence comparison 
* LCARs (Star Trek TNG) inspired web user interface for protein sequence work.

The code can be run via CLI/bash without using the web UI. However, the web UI makes exploring results easier. The web UI also can create, configure, start, stop and delete jobs, and monitor their progress.

## Current Status

Right now the part of SeqQuests most likely of interest is the /findings/ folder. 

* [Proposed updates](./findings/proposed_updates.md) to Swiss-Prot data files, based on an all-on-all comparison of proteins. 
* An [online browser](https://www.catalase.com/seqquests/match_explorer.html) with finds, alignments and sequence data files.

## Project Structure

```
/                            #
├─ c_src/                    # C++ and Metal source code
├─ data/                     # Small sample data files for development (not full data files)
├─ static/                   # HTML, CSS, JavaScript for the web interface
│  └─ match_explorer.html    #  Web UI to display sequence-pair lists and alignments
├─ findings/                 # Results found using the search
│  ├─ METHODS.md             #  Reproducing these results/findings
│  ├─ proposed_updates.md    #  My proposed Swiss-Prot annotation updates and alignments
│  ├─ sw_finds_distilled.txt #  Just the sequence-pairs for the above
│  ├─ sw_finds_standard.txt  #  A longer list of sequence-pairs
│  ├─ sw_finds_biased.txt    #  List of sequence-pairs with biased composition 
│  ├─ filter_reasons.txt     #  Stats for automatic reasons for dropping a sequence-pair
│  └─ gemini_comments.md     #  AI (caution required!) comments on the distilled similarities
├─ py/                       # Python scripts
│  ├─ ready_to_rock.py       #  Checks readiness; Sets up environment; Compiles code
│  ├─ sw_search.py           #  Performs all-on-all comparison
│  ├─ tree_builder.py        #  Reduces all-on-all results to a tree
│  ├─ filter_twilight.py     #  Automatic removal of known-already sequence-pairs
│  └─ web_server.py          #  Web browser front end
├─ docs/                     # Docs (work in progress).
│  ├─ explanations/          #  Background rather than how to
│  ├─ how-to/                #  Recipes organised by related topics
│  ├─ reference/             #  Settings for the various scripts 
│  └─ tutorials/             #  Tutorial content
├─ GETTING_STARTED.md        # How to set up the system
├─ LICENSE.md                # Copyright licenses
├─ CITATION.cff              # Citing this work
└─ README.md                 # This README
```

C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. 

## Links for AI Assistants
Much of the code was created with AI assistance (Claude, Gemini, Jules). AI also helped with tracking down many cases where protein similarities were already known.

AI assistants are guided to instructions they should follow by text like the text below:

See [docs/reference/specs/specs.md](./docs/reference/specs/specs.md) for IMPORTANT REQUIREMENTS for AI assistant work.

## Getting started

See [GETTING_STARTED.md](./GETTING_STARTED.md) in this directory for instructions on getting started.

