# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

SeqQuests provides:
* A very fast metal-accelerated Smith-Waterman local similarity search (2 days for 570,000 sequences all-on-all on Mac M4 Pro)
* Tooling for making, browsing and reducing an all-on-all Swissprot protein sequence comparison 
* LCARs (Star Trek TNG) inspired web user interface for protein sequence work.

The code can be run via CLI/bash without using the web UI. However, the web UI makes exploring results easier, by dynamically making alignments, ~~feature maps, and dotplots~~. The server also supports a user interface for jobs. You can create, configure, start, stop and delete jobs, and monitor their progress.

## Current Status

Right now the part of SeqQuests of most interest is likely to be the /findings/ folder. 

* [Proposed updates](./findings/proposed_updates.md) to SwissProt data files, based on an all-on-all comparison of proteins. 
* An [online browser](http://www.catalase.com/seqquests/match_explorer.html) with finds, alignments and sequence data files.

## Project Structure

```
/
├─ c_src/                     # C++ and Metal source code for accelerated computations.
├─ data/                      # Small sample data files for development (not full data files)
├─ findings/                  # Selected results found using the search
│  ├─ proposed_updates.md     # Specific annotation corrections
│  └─ sw_finds_distilled.txt  # 22 curated finds
├─ py/                        # Python source code for the application logic and web server.
├─ docs/                      # User documentation
│  ├─ explanations/           # SeqQuests splits explanations into for-users and for-devs
│  ├─ how-to/                 # Recipes organised by related topics
│  ├─ reference/              # Describes parameters for the various programs 
│  └─ tutorials/              # Tutorial content, foundations to special case uses.
└─ static/                    # Files for SeqQuests' web interface (HTML, CSS, JavaScript).
```

C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. The web UI falls back to using static files and sample data if the API endpoint is not available.

## Getting started

See /GETTING_STARTED.md in this directory and /docs/tutorials/getting_started.md for instructions on getting started.

## Links for AI Assistants
Much of the code was created with AI assistance (Claude, Gemini, Jules). AIs also helped with tracking down many cases where protein similarities were already known

AI assistants are guided to instructions they should follow by text like the text below:

See `/docs/reference/specs/specs.md` for IMPORTANT REQUIREMENTS for AI assistant work.

