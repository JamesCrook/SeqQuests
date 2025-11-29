# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

A FastAPI web server presents an interface to python and binary workers, which appear as jobs in the user interface. You can create, configure, start, stop and delete jobs, and monitor their progress.

The code can be run via CLI/bash without using the web UI. However, the web UI makes exploring results easier, by dynamically making dotplots and alignments.

SeqQuests provides:
* A very fast metal-accelerated Smith-Waterman local similarity search
* Tooling for making and reducing an all-on-all Swissprot protein sequence comparison (20 days for 570,000 sequences all-on-all on Mac M2 Pro)
* LCARs (Star Trek TNG) inspired user interface for browsing the hits.

## Project Structure

```
/
├── c_src/       # C and Metal source code for accelerated computations.
├── data/        # Small sample data files for development (not full data files)
├── py/          # Python source code for the application logic and web server.
├── specs/       # Project specification (for AI assistants to read).
└── static/      # Static assets for the web interface (HTML, CSS, JavaScript).
    └── docs/    # End user documentation
```

C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. The web UI falls back to using static files and sample data if the API endpoint is not available.


## For AI Assistants
See `/specs/test_strategy.md` for testing philosophy.
See `/specs/specs.md` for general coding approach.