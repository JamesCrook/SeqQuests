# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

A FastAPI web server presents an interface to python and binary workers, which appear as jobs in the user interface. You can create, configure, start, stop and delete jobs, and monitor their progress.

It provides:
* A very fast metal-accelerated Smith-Waterman local similarity search
* Tooling for making and reducing an all-on-all Swissprot protein sequence comparison (20 days for 570,000 sequences all-on-all on Mac M2 Pro)
* LCARs (Star Trek TNG) inspired user interface for browsing the hits.

## Project Structure

```
/
├── c_src/       # C and Metal source code for accelerated computations.
├── data/        # Small sample data files for development (not full data files)
├── metal/       # Python version of metal code, now superseded by the /c-src versions
├── py/          # Python source code for the application logic and web server.
├── specs/       # Project specification (for robots and AI to read).
├── static/      # Static assets for the web interface (HTML, CSS, JavaScript).
│   └── docs/    # End user documentation
└── test/        # Test scripts and resources.
```

The code can all be run as python scripts without using the web UI. C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. 
