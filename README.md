# SeqQuests

SeqQuests is a sequence analysis package.

SeqQuests provides:
* A fast metal-accelerated Smith-Waterman local similarity search (2 days for 570,000 sequences all-on-all on Mac M4 Pro)
* Tooling for making, browsing and reducing an all-on-all Swiss-Prot protein sequence comparison 
* LCARs (Star Trek TNG) inspired web user interface for protein sequence work.

The code can be run via CLI/bash without using the web UI. However, the web UI makes exploring results easier. The web UI also can create, configure, start, stop and delete jobs, and monitor their progress.

## Current Status

Right now the part of SeqQuests most likely of interest is the /findings/ folder. 

* [Proposed updates](./findings/proposed_updates.md) to Swiss-Prot data files, based on an all-on-all comparison of proteins. 
* An [online browser](http://www.catalase.com/seqquests/match_explorer.html) with finds, alignments and sequence data files.

## Project Structure

```
/
├─ c_src/                     # C++ and Metal source code.
├─ data/                      # Small sample data files for development (not full data files)
├─ findings/                  # Selected results found using the search
│  ├─ proposed_updates.md     # Specific annotation corrections
│  └─ sw_finds_distilled.txt  # 22 curated finds
├─ py/                        # Python scripts
├─ docs/                      # User documentation
│  ├─ explanations/           # Background rather than how to
│  ├─ how-to/                 # Recipes organised by related topics
│  ├─ reference/              # Settings for the various scripts 
│  └─ tutorials/              # Tutorial content
└─ static/                    # HTML, CSS, JavaScript for the web interface.
```

C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. 

## Links for AI Assistants
Much of the code was created with AI assistance (Claude, Gemini, Jules). AI also helped with tracking down many cases where protein similarities were already known.

AI assistants are guided to instructions they should follow by text like the text below:

See [docs/reference/specs/specs.md](./docs/reference/specs/specs.md) for IMPORTANT REQUIREMENTS for AI assistant work.

## Getting started

See [GETTING_STARTED.md](./GETTING_STARTED.md) in this directory for instructions on getting started.

